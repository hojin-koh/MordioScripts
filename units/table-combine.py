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

# Combine multiple tables, stacking the columns together
# Assumes each table contains the same set of keys

import csv
import sys

if sys.version_info < (3, 7):
    print("Error: minimum supported python version is 3.7 (for dict to preserve insertion order)", file=sys.stderr)
    sys.exit(37)

def addToRecord(mRecord, mFields, fieldKey, row):
    for field in mFields.keys():
        if field == fieldKey:
            mRecord[fieldKey] = row[fieldKey]
            continue
        mRecord[field] = row[field]

def main():
    fieldKey = None

    mData = {} # Use dict to preserve insertion order and to act as a set
    mFields = {} # Use dict to preserve insertion order and to act as a set
    for fname in sys.argv[1:]:
        with open(fname, encoding='utf-8') as fp:
            objReader = csv.DictReader(fp)
            if fieldKey is None:
                fieldKey = objReader.fieldnames[0]
            for field in objReader.fieldnames:
                mFields[field] = True
            for row in objReader:
                key = row[fieldKey] # It should crash if fieldKey is not present, which is exactly what we want here
                if key not in mData:
                    mData[key] = {}
                addToRecord(mData[key], objReader.fieldnames, fieldKey, row)

    sys.stdout.reconfigure(encoding='utf-8')
    objWriter = csv.DictWriter(sys.stdout, tuple(mFields.keys()), lineterminator="\n")
    objWriter.writeheader()

    for key in mData.keys():
        mVals = mData[key]
        objWriter.writerow(mVals)

if __name__ == '__main__':
    main()
