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
# Perform text normalization on text part of (id),(text) records (if sys.argv[2]=="text")
# or key part of (key),(number) records from stdin (if sys.argv[2]=="key")
# Also will do unicodedata.normalize()

import csv
import re
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
    mTrans = {}
    if len(sys.argv)>1:
        # Read the conversion table
        with open(sys.argv[1], encoding='utf-8') as fp:
            for row in csv.DictReader(fp):
                mTrans[row['before']] = row['after']
    objTrans = str.maketrans(mTrans)

    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')

    if sys.argv[2] == "text":
        objReader = csv.DictReader(sys.stdin)
        nameKey = objReader.fieldnames[0]
        nameText = objReader.fieldnames[1]
        objWriter = csv.DictWriter(sys.stdout, (nameKey, nameText), lineterminator="\n")
        objWriter.writeheader()
        for row in objReader:
            key = row[nameKey]
            text = normalize(objTrans, row[nameText].replace("\\n", "\n").strip())
            objWriter.writerow({nameKey: key, nameText: text.replace("\n", "\\n")})

    elif sys.argv[2] == "key":
        objReader = csv.DictReader(sys.stdin)
        nameKey = objReader.fieldnames[0]
        objWriter = csv.DictWriter(sys.stdout, objReader.fieldnames, lineterminator="\n")
        objWriter.writeheader()
        for row in objReader:
            row[nameKey] = normalize(objTrans, row[nameKey])
            objWriter.writerow(row)

if __name__ == '__main__':
    main()
