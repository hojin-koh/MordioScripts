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

# Output the nth dataset split file for cross-validation
# Using label as guidance in a stratified manner
# Stdin: label table (assuming 2nd field is the label)
# Arguments: n-split comb-id

import csv
import sys

from sklearn.model_selection import StratifiedKFold, StratifiedGroupKFold

def main():
    nSplit = int(sys.argv.pop(1))
    idx = int(sys.argv.pop(1))

    # TODO: implement the "group" part (will need some extra data input)
    if len(sys.argv) > 1:
        pass

    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    objReader = csv.DictReader(sys.stdin)
    fieldKey = objReader.fieldnames[0]
    fieldLabel = objReader.fieldnames[1]

    aOrder = []
    aLabel = []
    for row in objReader:
        aOrder.append(row[fieldKey])
        aLabel.append(row[fieldLabel])

    #TODO objCV = StratifiedGroupKFold(n_splits=nSplit, shuffle=True, random_state=0x19890604)
    objCV = StratifiedKFold(n_splits=nSplit, shuffle=True, random_state=0x19890604)
    rslt = objCV.split(aLabel, aLabel)
    # Go through the previous combinations without doing anything
    for i in range(idx):
        next(rslt)
    aTrain, aTest = next(rslt)
    sTrain = set(aTrain)
    sTest = set(aTest)
    print('ID={} nSplit={} nTrain={} nTest={}'.format(idx, nSplit, len(sTrain), len(sTest)), file=sys.stderr)

    # Output
    objWriter = csv.DictWriter(sys.stdout, (fieldKey, 'set'), lineterminator="\n")
    objWriter.writeheader()

    for i, key in enumerate(aOrder):
        if i in sTrain:
            objWriter.writerow({fieldKey: key, 'set': 'train'})
        else:
            objWriter.writerow({fieldKey: key, 'set': 'test'})

if __name__ == '__main__':
    main()
