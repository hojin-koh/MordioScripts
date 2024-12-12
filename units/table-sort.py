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

# Based on a series of tables containing data regarding the keys
# Perform sorting on the input table

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
    modeNumSort = False
    if sys.argv[1] == '--do-num-sort':
        modeNumSort = True
        sys.argv.pop(1)

    nameKey = sys.argv[1]
    nameSortKey = sys.argv[2]
    directionSort = sys.argv[3]

    mTable = {}
    for fname in (sys.argv[i] for i in range(4, len(sys.argv))):
        with open(fname, encoding='utf-8') as fp:
            objReader = csv.DictReader(fp)
            for row in objReader:
                key = row[nameKey] # It will crash if nameKey is not present, which is exactly what we want here
                mTable[key] = mTable.get(key, {}) | row

    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    objReader = csv.DictReader(sys.stdin)
    objWriter = csv.DictWriter(sys.stdout, objReader.fieldnames, lineterminator="\n")
    objWriter.writeheader()

    aTarget = []
    for row in objReader:
        key = row[nameKey] # It will crash if nameKey is not present, which is exactly what we want here
        if key not in mTable:
            continue
        aTarget.append(row)

    aTarget.sort(
            key=lambda m: float(mTable[m[nameKey]][nameSortKey]) if modeNumSort else m[nameSortKey],
            reverse=False if directionSort == 'asc' else True,
            )
    for row in aTarget:
        objWriter.writerow(row)

if __name__ == '__main__':
    main()
