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

# Check for classification accuracy given a space-separated label list
# When there are multiple labels in the label file, matching any one results in 100% accuracy
# (For real multi-label classification things, please use precision-recall)

import csv
import sys

def main():
    fieldOutput = sys.argv.pop(1)
    fieldRef = sys.argv.pop(1)
    fieldInput = sys.argv.pop(1)
    fileLabel = sys.argv.pop(1)

    mLabel = {}
    with open(fileLabel, "r", encoding='utf-8') as fp:
        objReader = csv.DictReader(fp)
        fieldKey = objReader.fieldnames[0]
        if len(fieldRef) == 0:
            fieldRef = objReader.fieldnames[1]
        for row in objReader:
            mLabel[row[fieldKey]] = set(row[fieldRef].strip().split())

    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    objReader = csv.DictReader(sys.stdin)
    fieldKey = objReader.fieldnames[0]
    if len(fieldInput) == 0:
        fieldInput = objReader.fieldnames[1]
    objWriter = csv.DictWriter(sys.stdout, (fieldKey, fieldOutput), lineterminator="\n")
    objWriter.writeheader()

    for row in objReader:
        key = row[fieldKey]
        if row[fieldInput] in mLabel[key]:
            acc = 1
        else:
            acc = 0
        objWriter.writerow({fieldKey: key, fieldOutput: acc})

if __name__ == '__main__':
    main()
