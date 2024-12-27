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

# Based on a table of (bad character),(good character) records as argv[1],
# Perform text normalization on text part of (id),(text) records (if sys.argv[1]=="text")
# or key part of (key),(number) records from stdin (if sys.argv[1]=="key")
# Also will do unicodedata.normalize()

import csv
import sys
import unicodedata

def normalize(objTrans, text):
    # Only normalize the "letter" parts, not punctuations
    return "".join(list(map(
        lambda c: unicodedata.normalize('NFKC', c).translate(objTrans)
        if unicodedata.category(c)[0] == 'L' else c,
        text
        )))

def main():
    modeConv = sys.argv.pop(1) # "text or key"
    if modeConv == 'text':
        fieldText = sys.argv.pop(1)

    mTrans = {}
    if len(sys.argv)>1:
        # Read the conversion table
        with open(sys.argv.pop(1), encoding='utf-8') as fp:
            objReader = csv.DictReader(fp)
            fieldConv1 = objReader.fieldnames[0]
            fieldConv2 = objReader.fieldnames[1]
            for row in objReader:
                mTrans[row[fieldConv1]] = row[fieldConv2]
    objTrans = str.maketrans(mTrans)

    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')

    if modeConv == "text":
        objReader = csv.DictReader(sys.stdin)
        fieldKey = objReader.fieldnames[0]
        if len(fieldText) == 0:
            fieldText = objReader.fieldnames[1]
        objWriter = csv.DictWriter(sys.stdout, (fieldKey, fieldText), lineterminator="\n")
        objWriter.writeheader()
        for row in objReader:
            key = row[fieldKey]
            text = normalize(objTrans, row[fieldText].replace("\\n", "\n").strip())
            objWriter.writerow({fieldKey: key, fieldText: text.replace("\n", "\\n")})
            sys.stdout.flush()

    elif modeConv == "key":
        objReader = csv.DictReader(sys.stdin)
        fieldKey = objReader.fieldnames[0]
        objWriter = csv.DictWriter(sys.stdout, objReader.fieldnames, lineterminator="\n")
        objWriter.writeheader()
        for row in objReader:
            row[fieldKey] = normalize(objTrans, row[fieldKey])
            objWriter.writerow(row)
            sys.stdout.flush()

if __name__ == '__main__':
    main()
