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
# Perform filtering on the input table

import csv
import re # Kept here for potential use in the expression
import sys

def addToRecord(mRecord, aFields, nameKey, row):
    for field in aFields:
        if field == nameKey:
            mRecord[nameKey] = row[nameKey]
            continue
        if field not in mRecord:
            mRecord[field] = []
        try:
            val = int(row[field])
        except:
            try:
                val = float(row[field])
            except:
                val = row[field]
        mRecord[field].append(val)

def main():
    modeOmit = False
    if sys.argv[1] == '--omit-absent-keys':
        modeOmit = True
        sys.argv.pop(1)
    nameKey = sys.argv[1]
    exprFilter = sys.argv[2]

    mData = {}
    for fname in (sys.argv[i] for i in range(3, len(sys.argv))):
        with open(fname, encoding='utf-8') as fp:
            objReader = csv.DictReader(fp)
            for row in objReader:
                key = row[nameKey] # It should crash if nameKey is not present, which is exactly what we want here
                if key not in mData:
                    mData[key] = {}
                addToRecord(mData[key], objReader.fieldnames, nameKey, row)

    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    objReader = csv.DictReader(sys.stdin)
    objWriter = csv.DictWriter(sys.stdout, objReader.fieldnames, lineterminator="\n")
    objWriter.writeheader()
    for row in objReader:
        key = row[nameKey] # It will crash if nameKey is not present, which is exactly what we want here
        if key not in mData:
            if not modeOmit:
                objWriter.writerow(row)
            continue
        record = mData[key]
        if eval(exprFilter):
            objWriter.writerow(row)

if __name__ == '__main__':
    main()
