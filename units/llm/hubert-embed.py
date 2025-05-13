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

# Do feature extraction on HuBERT

import csv
import io
import os
import sys
import tarfile

import numpy as np
import soundfile as sf
import torch
import torch.nn as nn
import torch.nn.functional as F

from torch.utils.data import IterableDataset, DataLoader
from transformers import HubertPreTrainedModel, HubertModel, AutoFeatureExtractor, WavLMPreTrainedModel, WavLMModel
from transformers.modeling_outputs import SequenceClassifierOutput

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
            hidden_states=pooled_output,
            attentions=outputs.attentions,
        )

class DatasetAudioIter(IterableDataset):
    def __init__(self, filePath):
        super().__init__()
        self.filePath = filePath

    def __iter__(self):
        fpTar = tarfile.open(self.filePath, mode='r|')
        for entry in fpTar:
            if entry.isdir(): continue
            key = entry.name
            # Read the wave file using a seekable buffer
            objWave = sf.SoundFile(io.BytesIO(fpTar.extractfile(entry).read()))
            data = objWave.read(dtype='float32')
            yield (key, data)

def getCollatorAudioIter(objProcessor):
    def CollateAudioIter(data):
        aKeys = tuple(v[0] for v in data)
        mtxData = objProcessor(
                [v[1] for v in data],
                sampling_rate=16000,
                return_tensors='pt',
                padding=True,
                ) #.to(torch.bfloat16)
        return (aKeys, mtxData)
    return CollateAudioIter

def main():
    dirModel = sys.argv.pop(1)

    # Load model
    objProcessor = AutoFeatureExtractor.from_pretrained(dirModel)
    #objModel = AutoModelForAudioClassification.from_pretrained(
    objModel = WavLMEmotion.from_pretrained(
            dirModel,
            classifier_proj_size=1024,
            #torch_dtype=torch.bfloat16,
            #attn_implementation="flash_attention_2",
            ).to('cuda')
    objModel = nn.DataParallel(objModel)

    # Load test data
    BATCH = 32
    datasetTest = DatasetAudioIter('/dev/stdin')
    fnCol = getCollatorAudioIter(objProcessor)
    loaderTest = DataLoader(datasetTest, batch_size=BATCH, shuffle=False, pin_memory=True, num_workers=1, collate_fn=fnCol)

    with tarfile.open(fileobj=sys.stdout.buffer, mode='w|') as fpwTar:
        for k,v in loaderTest:
            v = v.to('cuda')

            with torch.no_grad():
                mtxOutput = objModel(**v).hidden_states
            for j in range(mtxOutput.shape[0]):
                vEmbed = np.array(mtxOutput[j].cpu())
                fpwVector = io.BytesIO()
                np.save(fpwVector, vEmbed, allow_pickle=False)

                # New entry for writing
                entryNew = tarfile.TarInfo(k[j])
                entryNew.size = fpwVector.getbuffer().nbytes
                fpwVector.seek(0)
                fpwTar.addfile(entryNew, fileobj=fpwVector)

if __name__ == '__main__':
    main()
