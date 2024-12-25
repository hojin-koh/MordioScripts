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
# Do arithematic and output some new values

import csv
import sys

def addToRecord(mRecord, aFields, nameKey, row):
    for field in aFields:
        if field == nameKey:
            mRecord[nameKey] = row[nameKey]
            continue
        mRecord[field] = row[field]

def main():
    nameKey = sys.argv[1]

    mData = {}
    sKeys = set()
    aOrder = []
    sFields = set()
    aFields = []
    for fname in sys.argv[2:]:
        with open(fname, encoding='utf-8') as fp:
            objReader = csv.DictReader(fp)
            for field in objReader.fieldnames:
                if field not in sFields:
                    sFields.add(field)
                    aFields.append(field)
            for row in objReader:
                key = row[nameKey] # It should crash if nameKey is not present, which is exactly what we want here
                if key not in sKeys:
                    sKeys.add(key)
                    aOrder.append(key)
                if key not in mData:
                    mData[key] = {}
                addToRecord(mData[key], objReader.fieldnames, nameKey, row)

    sys.stdout.reconfigure(encoding='utf-8')
    objWriter = csv.DictWriter(sys.stdout, aFields, lineterminator="\n")
    objWriter.writeheader()

    for key in aOrder:
        mVals = mData[key]
        objWriter.writerow(mVals)

if __name__ == '__main__':
    main()
