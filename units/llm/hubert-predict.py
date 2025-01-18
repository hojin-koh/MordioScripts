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

# Predict from a HuBERT-based audio classifier

import csv
import io
import os
import sys
import tarfile

import soundfile as sf
import torch

from torch.utils.data import IterableDataset, DataLoader
from transformers import AutoModelForAudioClassification, AutoFeatureExtractor

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
                ).to(torch.bfloat16)
        return (aKeys, mtxData)
    return CollateAudioIter

def main():
    fieldOutput = os.environ.get('MORDIOSCRIPTS_FIELD_OUTPUT', 'pred')
    fieldKey = os.environ.get('MORDIOSCRIPTS_FIELD_KEY', 'id')

    dirModel = sys.argv.pop(1)
    nBest = int(sys.argv.pop(1))

    # Load model
    objProcessor = AutoFeatureExtractor.from_pretrained(dirModel)
    objModel = AutoModelForAudioClassification.from_pretrained(
            dirModel,
            torch_dtype=torch.bfloat16,
            attn_implementation="flash_attention_2",
            ).to('cuda')
    objModel = torch.nn.DataParallel(objModel)

    # Load label mapping from model
    mIdToLabel = {idx:l for l,idx in sorted(objModel.module.config.label2id.items(), key=lambda p: p[1])}
    nLabel = len(mIdToLabel)
    print(F"Labels({nLabel}):", ' '.join(mIdToLabel.values()) ,file=sys.stderr)

    # Prepare output
    sys.stdout.reconfigure(encoding='utf-8')
    aCols = [fieldKey]
    for i in range(nBest):
        aCols.append(F'{fieldOutput}{i+1}')
        aCols.append(F'{fieldOutput}{i+1}-score')
    aCols.append(F'{fieldOutput}-conf')
    objWriter = csv.DictWriter(sys.stdout, aCols, lineterminator="\n")
    objWriter.writeheader()

    # Load test data
    BATCH = 32
    datasetTest = DatasetAudioIter('/dev/stdin')
    fnCol = getCollatorAudioIter(objProcessor)
    loaderTest = DataLoader(datasetTest, batch_size=BATCH, shuffle=False, pin_memory=True, num_workers=1, collate_fn=fnCol)

    for k,v in loaderTest:
        v = v.to('cuda')

        with torch.no_grad():
            aaLogits = objModel(**v).logits.tolist()
        for j, aLogits in enumerate(aaLogits):
            aOut = [(mIdToLabel[idx], pred) for idx,pred in enumerate(aLogits)]
            aOut = sorted(aOut, key=lambda p: p[1], reverse=True)

            mOutput = {fieldKey: k[j], F'{fieldOutput}-conf': aOut[0][1]}
            for i in range(nBest):
                mOutput[F'{fieldOutput}{i+1}'] = aOut[i][0]
                mOutput[F'{fieldOutput}{i+1}-score'] = aOut[i][1]
            objWriter.writerow(mOutput)
        sys.stdout.flush()

if __name__ == '__main__':
    main()
