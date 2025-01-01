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
# Arguments: [--adversial group-file] output-files

import csv
import os
import sys

from sklearn.model_selection import StratifiedKFold, StratifiedGroupKFold

def main():
    fieldOutput = os.environ.get('MORDIOSCRIPTS_FIELD_OUTPUT', 'set')
    fieldRef = os.environ.get('MORDIOSCRIPTS_FIELD_LABEL', '')
    fieldGroup = os.environ.get('MORDIOSCRIPTS_FIELD_GROUP', '')

    modeAdversial = False
    if sys.argv[1] == '--adversial':
        sys.argv.pop(1)
        fileGroup = sys.argv.pop(1)
        mGroup = {}
        modeAdversial = True
        # TODO: implement adversial split
    # The remaining number of args decide how many splits we have
    nSplit = len(sys.argv[1:])

    sys.stdin.reconfigure(encoding='utf-8')
    objReader = csv.DictReader(sys.stdin)
    fieldKey = objReader.fieldnames[0]
    if not fieldRef:
        fieldRef = objReader.fieldnames[1]

    aOrder = []
    aLabel = []
    aGroup = []
    for row in objReader:
        aOrder.append(row[fieldKey])
        aLabel.append(row[fieldRef])
        if modeAdversial:
            pass # TODO

    if modeAdversial:
        objCV = StratifiedGroupKFold(n_splits=nSplit, shuffle=True, random_state=0x19890604)
        rslt = objCV.split(aLabel, aLabel, aGroup)
    else:
        objCV = StratifiedKFold(n_splits=nSplit, shuffle=True, random_state=0x19890604)
        rslt = objCV.split(aLabel, aLabel)

    for idx, fname in enumerate(sys.argv[1:]):
        aTrain, aTest = next(rslt)
        sTrain, sTest = set(aTrain), set(aTest)
        print('ID={} nSplit={} nTrain={} nTest={}'.format(idx, nSplit, len(sTrain), len(sTest)), file=sys.stderr)

        with open(fname, 'w', encoding='utf-8') as fpw:
            objWriter = csv.DictWriter(fpw, (fieldKey, fieldOutput), lineterminator="\n")
            objWriter.writeheader()

            for i, key in enumerate(aOrder):
                if i in sTrain:
                    objWriter.writerow({fieldKey: key, fieldOutput: 'train'})
                else:
                    objWriter.writerow({fieldKey: key, fieldOutput: 'test'})

if __name__ == '__main__':
    main()
