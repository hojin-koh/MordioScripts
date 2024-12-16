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

# Train a BERT-based classifier

import csv
import os
import sys

import torch

from transformers import Trainer, TrainingArguments
from sklearn.model_selection import train_test_split

os.environ['TQDM_MININTERVAL'] = '2'
os.environ['TQDM_SMOOTHING'] = '0'
os.environ['TQDM_DYNAMIC_NCOLS'] = '1'

def computeMetricHF(pred):
    aPreds = pred.predictions.argmax(-1)
    aLabels = pred.label_ids
    n = len(aLabels)
    nCorrect = 0
    for i in range(n):
        if aLabels[i] == aPreds[i]:
            nCorrect += 1

    return {
            'acc': 1.0 * nCorrect / n,
            }

class DatasetTraining(torch.utils.data.Dataset):
    def __init__(self, objTok, aData):
        self.m_data = objTok([t for t,l in aData], truncation=True, padding=True)
        self.m_aLabels = [l for t,l in aData]

    def __len__(self):
        return len(self.m_aLabels)

    def __getitem__(self, idx):
        rtn = {k: torch.tensor(v[idx]) for k,v in self.m_data.items()}
        rtn['labels'] = torch.tensor([self.m_aLabels[idx]])
        return rtn

def main():
    dirOutput = sys.argv[1]

    typeModel = sys.argv[2] # BERT
    nameModel = sys.argv[3] # google-bert/bert-base-multilingual-cased

    fileLabel = sys.argv[4]

    mLabel = {}

    # Load and number the labels
    with open(fileLabel, 'r', encoding='utf-8') as fp:
        objReader = csv.DictReader(fp)
        nameKey = objReader.fieldnames[0]
        nameLabel = objReader.fieldnames[1]
        for row in objReader:
            mLabel[row[nameKey]] = row[nameLabel]
    mLabelToId = {l:i for i,l in enumerate(sorted(set(mLabel.values())))}

    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    objReader = csv.DictReader(sys.stdin)
    nameKey = objReader.fieldnames[0]
    nameText = objReader.fieldnames[1]

    aDataTrainAll = []
    for row in objReader:
        text = row[nameText].replace('\\n', '\n').strip()
        idLabel = mLabelToId[mLabel[row[nameKey]]]
        aDataTrainAll.append((text, idLabel))

    # 90% train, 10% valid
    aDataTrain, aDataDev = train_test_split(aDataTrainAll, test_size=0.1, random_state=0x19890604, stratify=[l for t,l in aDataTrainAll])

    # Now we need to tokenize things, start loading models
    if typeModel == "BERT":
        from transformers import BertTokenizerFast, BertForSequenceClassification
        Tokenizer = BertTokenizerFast
        ClassModel = BertForSequenceClassification
    else:
        raise NameError(F"Invalid model type: {typeModel}")

    # Get our tokenizer and save a copy—will need it later
    objTok = Tokenizer.from_pretrained(nameModel, do_lower_case=False, clean_up_tokenization_spaces=False)
    objTok.save_pretrained(dirOutput)

    dataTrain = DatasetTraining(objTok, aDataTrain)
    dataDev = DatasetTraining(objTok, aDataDev)

    objModel = ClassModel.from_pretrained(nameModel,
                                          num_labels=len(mLabelToId),
                                          id2label={i:l for l,i in mLabelToId.items()},
                                          label2id=mLabelToId,
                                          ).to('cuda')

    print(objModel, file=sys.stderr)
    print("Train Sample Size: {}".format(len(aDataTrain)), file=sys.stderr)
    print("Validation Sample Size: {}".format(len(aDataDev)), file=sys.stderr)

    argTrain = TrainingArguments(
            output_dir=F'tmp/hfoutputs-{os.getpid()}',
            save_strategy="epoch",
            save_total_limit=2,
            load_best_model_at_end=True,
            logging_dir=F'tmp/hfoutputs-{os.getpid()}',
            logging_strategy="epoch",
            logging_first_step=True,
            eval_strategy="epoch",
            eval_on_start=False,
            metric_for_best_model="acc",
            auto_find_batch_size=True,
            per_device_train_batch_size=64,
            per_device_eval_batch_size=64,
            num_train_epochs=15,
            warmup_ratio=0.1,
            )

    objTrainer = Trainer(
            model=objModel,
            args=argTrain,
            train_dataset=dataTrain,
            eval_dataset=dataDev,
            compute_metrics=computeMetricHF,
            )
    print(objTrainer.evaluate(), file=sys.stderr)
    objTrainer.train()
    print(objTrainer.evaluate(), file=sys.stderr)

    objTrainer.save_model(dirOutput)
    print("Best model saved: {}".format(dirOutput), file=sys.stderr)

if __name__ == '__main__':
    main()
