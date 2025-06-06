#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2020-2024, Hojin Koh
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Train a HuBERT-based audio classifier

import csv
import io
import os
import sys
import tarfile

from collections import Counter
from math import ceil

import numpy as np
import soundfile as sf
import torch
import torch.nn as nn
import torch.nn.functional as F

from tqdm import tqdm

from torch.optim.lr_scheduler import ExponentialLR, ReduceLROnPlateau, CosineAnnealingWarmRestarts
from torch.utils.data import Dataset, DataLoader
from transformers import HubertPreTrainedModel, HubertModel, AutoFeatureExtractor, WavLMPreTrainedModel, WavLMModel
from transformers.modeling_outputs import SequenceClassifierOutput
from pytorch_warmup import UntunedExponentialWarmup

from MordioScripts.misc import overrideTqdmDefaults

overrideTqdmDefaults()

class AttentiveStatisticsPooling(nn.Module):
    """
    AttentiveStatisticsPooling
    Paper: Attentive Statistics Pooling for Deep Speaker Embedding
    Link: https://arxiv.org/pdf/1803.10963.pdf
    """
    def __init__(self, input_size):
        super().__init__()
        self._indim = input_size
        self.sap_linear = nn.Linear(input_size, input_size)
        self.attention = nn.Parameter(torch.rand(input_size, 1).to(torch.float32))#.to(torch.bfloat16))
        torch.nn.init.normal_(self.attention, mean=0, std=1)

    def forward(self, xs, mask, mask2):
        """
        xs: (batch_size, T, feat_dim)
        mask: (batch_size, T)

        => output: (batch_size, feat_dim*2)
        """
        feat_lens = mask.sum(dim=1).tolist()
        pooled_list = []
        for x, feat_len in zip(xs, feat_lens):
            x = x[:feat_len].unsqueeze(0)
            h = torch.tanh(self.sap_linear(x))
            w = torch.matmul(h, self.attention).squeeze(dim=2)
            w = F.softmax(w, dim=1).view(x.size(0), x.size(1), 1)
            mu = torch.sum(x * w, dim=1)
            rh = torch.sqrt((torch.sum((x**2) * w, dim=1) - mu**2).clamp(min=1e-5))
            x = torch.cat((mu, rh), 1).squeeze(0)
            pooled_list.append(x)

        return torch.stack(pooled_list)

#class HubertEmotion(HubertPreTrainedModel):
class WavLMEmotion(WavLMPreTrainedModel):
    def __init__(self, config):
        super().__init__(config)
        #self.hubert = HubertModel(config)
        self.wavlm = WavLMModel(config)

        p = 0.5 # dropout
        self.pooler = AttentiveStatisticsPooling(config.hidden_size)
        num_layers = config.num_hidden_layers + 1  # transformer layers + input embeddings
        if config.use_weighted_layer_sum:
            self.layer_weights = nn.Parameter(torch.ones(num_layers) / num_layers)
        self.classifier = nn.Sequential(
                nn.Dropout(p),
                nn.Linear(config.hidden_size*2, config.classifier_proj_size),
                nn.LayerNorm(config.classifier_proj_size),
                nn.ReLU(),
                nn.Dropout(p),
                nn.Linear(config.classifier_proj_size, config.num_labels),
                )

        # Freeze the feature encoder part
        #self.hubert.feature_extractor._freeze_parameters()
        self.wavlm.feature_extractor._freeze_parameters()

        # Initialize weights and apply final processing
        self.post_init()

    def forward(
            self,
            input_values,
            attention_mask=None,
            output_attentions=None,
            output_hidden_states=None,
            return_dict=None,
            ):
        return_dict = return_dict if return_dict is not None else self.config.use_return_dict
        output_hidden_states = True if self.config.use_weighted_layer_sum else output_hidden_states

        outputs = self.wavlm(
            input_values,
            attention_mask=attention_mask,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )

        _HIDDEN_STATES_START_POSITION = 2
        if self.config.use_weighted_layer_sum:
            hidden_states = outputs[_HIDDEN_STATES_START_POSITION]
            hidden_states = torch.stack(hidden_states, dim=1)
            norm_weights = nn.functional.softmax(self.layer_weights, dim=-1)
            hidden_states = (hidden_states * norm_weights.view(-1, 1, 1)).sum(dim=1)
        else:
            hidden_states = outputs[0]

        padding_mask = self._get_feature_vector_attention_mask(hidden_states.shape[1], attention_mask)
        pooled_output = self.pooler(hidden_states, mask=padding_mask, mask2=attention_mask)

        logits = self.classifier(pooled_output)

        if not return_dict:
            output = (logits,) + outputs[_HIDDEN_STATES_START_POSITION:]
            return ((loss,) + output) if loss is not None else output

        return SequenceClassifierOutput(
            logits=logits,
            hidden_states=outputs.hidden_states,
            attentions=outputs.attentions,
        )

class DatasetAudioLabeled(Dataset):
    def __init__(self, mData, mLabel):
        super().__init__()
        self.aKeys = tuple(mData.keys())
        self.mData = mData
        self.mLabel = mLabel

    def __len__(self):
        return len(self.aKeys)

    def __getitem__(self, idx):
        key = self.aKeys[idx]
        return (self.mData[key], self.mLabel[key])

def getCollatorAudioLabeled(objProcessor):
    def CollateAudioLabeled(data):
        mtxData = objProcessor(
                [v[0] for v in data],
                sampling_rate=16000,
                return_tensors='pt',
                padding=True,
                ) #.to(torch.bfloat16)
        vLabels = torch.tensor([v[1] for v in data], dtype=torch.long)
        return (mtxData, vLabels)
    return CollateAudioLabeled


def main():
    fieldRef = os.environ.get('MORDIOSCRIPTS_FIELD_LABEL', '')

    dirOutput = sys.argv.pop(1)
    typeModel = sys.argv.pop(1) # HuBERT
    nameModel = sys.argv.pop(1) # facebook/hubert-large-ls960-ft

    fileDev = sys.argv.pop(1)
    fileLabel = sys.argv.pop(1)

    # Load and number the labels
    mLabel = {}
    with open(fileLabel, 'r', encoding='utf-8') as fp:
        objReader = csv.DictReader(fp)
        fieldKey = objReader.fieldnames[0]
        if not fieldRef:
            fieldRef = objReader.fieldnames[1]
        for row in objReader:
            mLabel[row[fieldKey]] = row[fieldRef]
    mLabelToId = {l:i for i,l in enumerate(sorted(set(mLabel.values())))}
    mLabel = {k: mLabelToId[l] for k,l in mLabel.items()} # Convert to id
    nLabel = len(mLabelToId)
    print(F"Labels({nLabel}):", ' '.join(mLabelToId.keys()) ,file=sys.stderr)

    mDataTrain = {}
    mDataDev = {}

    # Load dev data
    fpTar = tarfile.open(fileDev, mode='r|')
    for entry in fpTar:
        if entry.isdir(): continue
        # Read the wave file using a seekable buffer
        objWave = sf.SoundFile(io.BytesIO(fpTar.extractfile(entry).read()))
        data = objWave.read(dtype='float32')
        mDataDev[entry.name] = data
    nDataDev = len(mDataDev)

    print("Dev Sample Size: {}".format(nDataDev), file=sys.stderr)

    # Load train data
    fpTar = tarfile.open(fileobj=sys.stdin.buffer, mode='r|')
    for entry in fpTar:
        if entry.isdir(): continue
        # Read the wave file using a seekable buffer
        objWave = sf.SoundFile(io.BytesIO(fpTar.extractfile(entry).read()))
        data = objWave.read(dtype='float32')
        mDataTrain[entry.name] = data
    nDataTrain = len(mDataTrain)

    print("Train Sample Size: {}".format(nDataTrain), file=sys.stderr)

    # Calculate class weight
    vCountClass = Counter(v for k,v in mLabel.items() if k in mDataTrain)  # Get counts of each label
    vCountClass = np.array([v for i,v in sorted(vCountClass.items())], dtype=np.float64)
    vWeightClass = 1 / vCountClass
    vWeightClass /= np.sum(vWeightClass)
    print("Label Weights:", ' '.join(F"{w:.4f}" for w in vWeightClass), file=sys.stderr)


    # Now we need to prepare things, start loading models
    if typeModel == "HuBERT":
        ClassModel = HubertEmotion
    elif typeModel == "WavLM":
        ClassModel = WavLMEmotion
    else:
        raise NameError(F"Invalid model type: {typeModel}")

    objProcessor = AutoFeatureExtractor.from_pretrained(nameModel)
    objModel = ClassModel.from_pretrained(
            nameModel,
            num_labels=nLabel,
            classifier_proj_size=1024,
            #use_weighted_layer_sum=True,
            id2label={i:l for l,i in mLabelToId.items()},
            label2id=mLabelToId,
            #torch_dtype=torch.bfloat16,
            #attn_implementation="flash_attention_2",
            ).to('cuda')
    print(objModel, file=sys.stderr)

    objModel = nn.DataParallel(objModel)
    objProcessor.save_pretrained(dirOutput)

    # Get our tokenizer and save a copy—will need it later
    BATCH = 32
    datasetTrain = DatasetAudioLabeled(mDataTrain, mLabel)
    datasetDev = DatasetAudioLabeled(mDataDev, mLabel)
    fnCol = getCollatorAudioLabeled(objProcessor)
    loaderTrain = DataLoader(datasetTrain, batch_size=BATCH, shuffle=True, pin_memory=True, num_workers=1, collate_fn=fnCol)
    loaderDev = DataLoader(datasetDev, batch_size=BATCH, shuffle=False, pin_memory=True, num_workers=1, collate_fn=fnCol)

    ACCUM = 1
    stepPerEpoch = ceil(ceil(nDataTrain/BATCH)/ACCUM)
    NUM_EPOCH_WARMUP = ceil(1000/stepPerEpoch)*3
    NUM_ANNEAL_CYCLE = 5
    NUM_EPOCH_NORMAL = 2**NUM_ANNEAL_CYCLE-1 # 1+2+4+8+...
    NUM_EPOCH = NUM_EPOCH_WARMUP + NUM_EPOCH_NORMAL

    LR=2e-5
    objOpt = torch.optim.AdamW(objModel.parameters(), lr=LR, fused=True)
    objOpt.zero_grad(set_to_none=True)
    #fnLoss = nn.CrossEntropyLoss(weight=torch.tensor(vWeightClass, dtype=torch.float32).to('cuda')) #, dtype=torch.bfloat16
    fnLoss = nn.CrossEntropyLoss()
    objSchedExp = ExponentialLR(objOpt, 0.95)
    objSchedCos = CosineAnnealingWarmRestarts(objOpt, T_0=stepPerEpoch, eta_min=LR/1000, T_mult=2)
    #objSchedPlateau = ReduceLROnPlateau(objOpt, factor=0.5, patience=5)
    objSchedWarmup = UntunedExponentialWarmup(objOpt)

    print(F"Total Epoch: {NUM_EPOCH} ({NUM_EPOCH_WARMUP} warmup) {stepPerEpoch} steps per epoch", file=sys.stderr)

    # Main training loop
    pbar = tqdm(total=(nDataTrain+nDataDev)*NUM_EPOCH)
    minLoss = 1e100
    for epoch in range(1,NUM_EPOCH+1):
        objModel.train()
        lrInit = objOpt.param_groups[0]['lr']
        meanLoss = 0
        nSample = 0
        for v,l in loaderTrain:
            v,l = v.to('cuda'), l.to('cuda')
            pred = objModel(**v)
            loss = fnLoss(pred.logits, l) / ACCUM

            nSampleThis = pred.logits.shape[0]
            nSample += nSampleThis
            meanLoss += (loss.item() - meanLoss) * nSampleThis / nSample

            loss.backward()
            if nSample % (BATCH*ACCUM) == 0 or nSampleThis != BATCH:
                objOpt.step()
                objOpt.zero_grad(set_to_none=True)
                lrThis = objOpt.param_groups[0]['lr']
                with objSchedWarmup.dampening():
                    if epoch > NUM_EPOCH_WARMUP:
                        objSchedCos.step()
            pbar.update(nSampleThis)

        objModel.eval()
        meanLossDev = 0
        nSample = 0
        with torch.no_grad():
            for v,l in loaderDev:
                v,l = v.to('cuda'), l.to('cuda')
                pred = objModel(**v)
                loss = fnLoss(pred.logits, l)
                nSampleThis = pred.logits.shape[0]
                nSample += nSampleThis
                meanLossDev += (loss.item() - meanLossDev) * nSampleThis / nSample
                pbar.update(nSampleThis)

        if epoch > NUM_EPOCH_WARMUP:
            with objSchedWarmup.dampening():
                objSchedExp.step()
                #objSchedPlateau.step(meanLossDev)

        objModel.module.save_pretrained(F"{dirOutput}/{epoch}")
        if meanLossDev < minLoss*1.001:
            msgSave = " (Save)"
            minLoss = meanLossDev
            objModel.module.save_pretrained(dirOutput)
        else:
            msgSave = ""
        pbar.write(F"\033[2K\rEpoch {epoch} lr {lrInit:.2E} -> {lrThis:.2E} loss {meanLoss:.4f} devloss {meanLossDev:.4f}{msgSave}", file=sys.stderr)

if __name__ == '__main__':
    main()
