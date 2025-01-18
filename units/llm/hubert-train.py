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

from tqdm import tqdm

from torch.optim.lr_scheduler import ExponentialLR, ReduceLROnPlateau, CosineAnnealingWarmRestarts
from torch.utils.data import Dataset, DataLoader
from pytorch_warmup import UntunedExponentialWarmup

from MordioScripts.misc import overrideTqdmDefaults

overrideTqdmDefaults()

class ProgressiveCrossEntropy(torch.nn.CrossEntropyLoss):
    # epoch and epochTotal are 1-based index
    def __init__(self, vCountClass, epoch, epochTotal, kStart=1, kEnd=6):
        k = (epoch-1)/(epochTotal-1) * (kEnd-kStart)+kStart
        vWeightClass = (1 - (1-0.1**k)**vCountClass) / (1 - (1-0.1**k))
        vWeightClass /= np.sum(vWeightClass)
        super().__init__(weight=torch.tensor(vWeightClass, dtype=torch.bfloat16).to('cuda'))

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
                ).to(torch.bfloat16)
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

    # Calculate class weight
    vCountClass = Counter(mLabel.values())  # Get counts of each label
    vCountClass = np.array([v for i,v in sorted(vCountClass.items())], dtype=np.float64)
    vWeightClass = 1 / vCountClass
    vWeightClass /= np.sum(vWeightClass)
    print("Label Weights:", ' '.join(F"{w:.4f}" for w in vWeightClass), file=sys.stderr)

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

    # Now we need to prepare things, start loading models
    if typeModel == "HuBERT":
        from transformers import HubertForSequenceClassification, AutoFeatureExtractor
        objProcessor = AutoFeatureExtractor.from_pretrained(nameModel)
        objModel = HubertForSequenceClassification.from_pretrained(
                nameModel,
                num_labels=nLabel,
                id2label={i:l for l,i in mLabelToId.items()},
                label2id=mLabelToId,
                torch_dtype=torch.bfloat16,
                attn_implementation="flash_attention_2",
                ).to('cuda')
    else:
        raise NameError(F"Invalid model type: {typeModel}")

    objModel = torch.nn.DataParallel(objModel)
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
    NUM_EPOCH_ANNEAL = 2**(NUM_ANNEAL_CYCLE) - 1 # 1+2+4+...
    NUM_EPOCH = NUM_EPOCH_WARMUP + NUM_EPOCH_ANNEAL

    LR=2e-5
    objOpt = torch.optim.AdamW(objModel.parameters(), lr=LR, fused=True)
    objOpt.zero_grad(set_to_none=True)
    fnLossDev = torch.nn.CrossEntropyLoss(weight=torch.tensor(vWeightClass, dtype=torch.bfloat16).to('cuda'))
    objSchedExp = ExponentialLR(objOpt, 0.95)
    #objSchedCos = CosineAnnealingWarmRestarts(objOpt, T_0=stepPerEpoch, eta_min=LR/1000, T_mult=2)
    #objSched2 = ReduceLROnPlateau(objOpt, factor=0.4, patience=4)
    objSchedWarmup = UntunedExponentialWarmup(objOpt)

    print(F"Total Epoch: {NUM_EPOCH} ({NUM_EPOCH_WARMUP} warmup) {stepPerEpoch} steps per epoch", file=sys.stderr)

    # Main training loop
    pbar = tqdm(total=(nDataTrain+nDataDev)*NUM_EPOCH)
    minLoss = 1e100
    for epoch in range(1,NUM_EPOCH+1):
        objModel.train()
        fnLossTrain = ProgressiveCrossEntropy(vCountClass, epoch, NUM_EPOCH)
        lrInit = objOpt.param_groups[0]['lr']
        meanLoss = 0
        nSample = 0
        for v,l in loaderTrain:
            v,l = v.to('cuda'), l.to('cuda')
            pred = objModel(**v)
            loss = fnLossTrain(pred.logits, l) / ACCUM

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
                        #objSchedCos.step()
                        pass
            pbar.update(nSampleThis)

        if epoch > NUM_EPOCH_WARMUP:
            with objSchedWarmup.dampening():
                objSchedExp.step()

        objModel.eval()
        meanLossDev = 0
        nSample = 0
        with torch.no_grad():
            for v,l in loaderDev:
                v,l = v.to('cuda'), l.to('cuda')
                pred = objModel(**v)
                loss = fnLossDev(pred.logits, l)
                nSampleThis = pred.logits.shape[0]
                nSample += nSampleThis
                meanLossDev += (loss.item() - meanLossDev) * nSampleThis / nSample
                pbar.update(nSampleThis)

        if meanLossDev < minLoss:
            msgSave = " (Save)"
            minLoss = meanLossDev
            objModel.module.save_pretrained(dirOutput)
        else:
            msgSave = ""
        pbar.write(F"\033[2K\rEpoch {epoch} lr {lrInit:.2E} -> {lrThis:.2E} loss {meanLoss:.4f} devloss {meanLossDev:.4f}{msgSave}", file=sys.stderr)

if __name__ == '__main__':
    main()
