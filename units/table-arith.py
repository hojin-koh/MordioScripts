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
import re # Kept here for potential use in the expression
import sys

def addToRecord(mRecord, aFields, fieldKey, row):
    for field in aFields:
        if field == fieldKey:
            mRecord[fieldKey] = row[fieldKey]
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
    fieldKey = None

    mData = {}
    while len(sys.argv) > 1:
        fname = sys.argv.pop(1)
        if fname == '--':
            break
        with open(fname, encoding='utf-8') as fp:
            objReader = csv.DictReader(fp)
            if fieldKey is None:
                fieldKey = objReader.fieldnames[0]
            for row in objReader:
                key = row[fieldKey] # It should crash if fieldKey is not present, which is exactly what we want here
                if key not in mData:
                    mData[key] = {}
                addToRecord(mData[key], objReader.fieldnames, fieldKey, row)

    aFields = []
    aExprs = []
    while len(sys.argv) > 1:
        aFields.append(sys.argv.pop(1))
        aExprs.append(sys.argv.pop(1))

    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    objReader = csv.DictReader(sys.stdin)
    objWriter = csv.DictWriter(sys.stdout, (fieldKey, *aFields), lineterminator="\n")
    objWriter.writeheader()
    for row in objReader:
        key = row[fieldKey] # It will crash if fieldKey is not present, which is exactly what we want here
        if key not in mData:
            if modeOmit:
                continue
        data = mData[key] # It will crash if not modeOmit and key not in mData, failing early and visibly
        mVal = {fieldKey: key}
        for i in range(len(aFields)):
            try:
                mVal[aFields[i]] = eval(aExprs[i])
            except Exception as e:
                print(e, file=sys.stderr)
                print(data, file=sys.stderr)
                sldkjflksdjf
        objWriter.writerow(mVal)

if __name__ == '__main__':
    main()
