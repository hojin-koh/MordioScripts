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

# Interpolate tables given in sys.argv like this: weight1 file1 weight2 file2 ...
# If --normalize is specified before all other arguments, normalize to the sum of 1st file

import csv
import sys

from math import ceil

if sys.version_info < (3, 7):
    print("Error: minimum supported python version is 3.7 (for dict to preserve insertion order)", file=sys.stderr)
    sys.exit(37)

def main():
    modeNormalize = False
    if sys.argv[1] == '--normalize':
        modeNormalize = True
        sys.argv.pop(1)
    fieldKey = None

    isFloat = False
    aCnt = [] # Recording the total sum of each table
    amTable = [] # This should preserve insertion order in python 3.7+

    for w, fname in ((float(sys.argv[i]), sys.argv[i+1]) for i in range(1, len(sys.argv), 2)):
        amTable.append({})
        mTable = amTable[-1]
        cntThis = 0

        with open(fname, encoding='utf-8') as fp:
            objReader = csv.DictReader(fp)
            fieldKey = objReader.fieldnames[0]
            fieldValue = objReader.fieldnames[1]

            for row in objReader:
                key = row[fieldKey]
                if fieldValue not in row:
                    sys.stderr.write("Warning: entry {} has no column {}, skipped\n".format(key, fieldValue))
                    continue
                strVal = row[fieldValue]

                if strVal.find('.') != -1:
                    val = float(strVal.strip())
                    isFloat = True
                else:
                    val = int(strVal.strip())

                cntThis += val
                val *= 1.0 * w # Force into float

                if key not in mTable:
                    mTable[key] = val
                else:
                    mTable[key] += val

        aCnt.append(cntThis)

    # Normalize each table, then add to the overall table
    mTable = {}
    for i, (cnt, mTableThis) in enumerate(zip(aCnt, amTable)):
        for key in amTable[i].keys():
            if key not in mTable:
                mTable[key] = 0
            if modeNormalize:
                mTable[key] += mTableThis[key] / cnt * aCnt[0]
            else:
                mTable[key] += mTableThis[key]

    # Configure output
    sys.stdout.reconfigure(encoding='utf-8')
    objWriter = csv.DictWriter(sys.stdout, (fieldKey, fieldValue), lineterminator="\n")
    objWriter.writeheader()

    # Output
    if isFloat:
        for k in mTable.keys():
            v = mTable[k]
            objWriter.writerow({fieldKey: k, fieldValue: v})
    else:
        for k in mTable.keys():
            v = mTable[k]
            objWriter.writerow({fieldKey: k, fieldValue: ceil(v)})

if __name__ == '__main__':
    main()
