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

# Predict class from a BERT-based classifier
# Usage: bertclass-predict.py <model>

import csv
import sys

import torch

from transformers import pipeline

def main():
    dirModel = sys.argv[1]
    nBest = int(sys.argv[2])

    # TODO may want to switch to energy-based ood detection later, with function_to_apply='none' to disable softmax
    try:
        objPipeline = pipeline('text-classification', model=dirModel, tokenizer=dirModel, device='cuda')
        print(F"Loaded transformer model from {dirModel}", file=sys.stderr)
    except:
        objPipeline = pipeline('text-classification', model=dirModel, tokenizer=dirModel)
        print(F"Loaded transformer model from {dirModel} in CPU", file=sys.stderr)

    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    objReader = csv.DictReader(sys.stdin)
    nameKey = objReader.fieldnames[0]
    nameText = objReader.fieldnames[1]

    aCols = [nameKey]
    for i in range(nBest):
        aCols.append(F'pred{i+1}')
        aCols.append(F'score{i+1}')
    aCols.append('conf')
    objWriter = csv.DictWriter(sys.stdout, aCols, lineterminator="\n")
    objWriter.writeheader()

    for row in objReader:
        key = row[nameKey]
        text = row[nameText].replace("\\n", "\n").strip()
        mRslt = objPipeline(text, top_k=None, padding=True, truncation=True)
        aOut = [(l['label'], l['score']) for l in mRslt]
        mOutput = {nameKey: key, 'conf': aOut[0][1]}
        for i in range(nBest):
            mOutput[F'pred{i+1}'] = aOut[i][0]
            mOutput[F'score{i+1}'] = aOut[i][1]
        objWriter.writerow(mOutput)
        # TODO energy-based confidence score
        #energy = torch.sigmoid(torch.logsumexp(torch.tensor(tuple(l['score'] for l in mRslt)), dim=0))

if __name__ == '__main__':
    main()