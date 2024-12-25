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

# Compute bootstrapped mean and 95% confidence interval from input table
# When multiple table are added, assume each table get exactly the same weight
# If you don't want this behaviour, concat the tables beforehand

import csv
import sys

import numpy as np
from scipy.stats import bootstrap

# Define the weighted mean function
def meanWeighted(aSamples, aWeights):
    return np.average(aSamples, weights=aWeights)

def main():
    aFields = sys.argv[1].strip().split(',') if len(sys.argv[1]) > 0 else None
    tagOutput = sys.argv[2]

    if aFields is not None:
        maData = {field: [] for field in aFields}
    else:
        maData = {} # Will be initialized later
    aWeights = []
    for fname in sys.argv[3:]:
        nData = 0
        with open(fname, "r", encoding='utf-8') as fp:
            objReader = csv.DictReader(fp)
            if aFields is None:
                aFields = objReader.fieldnames[1:]
                maData = {field: [] for field in aFields}
            for row in objReader:
                nData += 1
                for field in aFields:
                    maData[field].append(float(row[field]))
        for i in range(nData):
            aWeights.append(100.0/nData)

    # Actually compute the bootstrap things
    mOutput = {'tag': tagOutput}
    vWeights = np.array(aWeights)
    print(F"=== Tag {tagOutput} ===", file=sys.stderr)
    for field in aFields:
        rslt = bootstrap(
                (np.array(maData[field]), vWeights),
                statistic=meanWeighted,
                paired=True,
                confidence_level=0.95,
                )
        mean = rslt.bootstrap_distribution.mean()
        lower, upper = rslt.confidence_interval
        print(F"{field}: {mean:.6f} ({lower:.6f} ~ {upper:.6f})", file=sys.stderr)
        mOutput[field] = mean
        mOutput[F'{field}-95l'] = lower
        mOutput[F'{field}-95u'] = upper

    sys.stdout.reconfigure(encoding='utf-8')
    aCols = ['tag']
    for field in aFields:
        aCols.append(field)
        aCols.append(F'{field}-95l')
        aCols.append(F'{field}-95u')
    objWriter = csv.DictWriter(sys.stdout, aCols, lineterminator="\n")
    objWriter.writeheader()
    objWriter.writerow(mOutput)

if __name__ == '__main__':
    main()
