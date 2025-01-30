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

if sys.version_info < (3, 7):
    print("Error: minimum supported python version is 3.7 (for dict to preserve insertion order)", file=sys.stderr)
    sys.exit(37)

# Note that scipy.stats.bootstrap will give our function data in this shape:
# n parameters each is an np.array of (nResample, nSample)
# if only 1 sample, n parameters each is an np.array of (nSample,)
def getClassifierStats(*aSamples, axis=-1):
    nLabel = (len(aSamples)-1)//3
    mtxWeight = 1.0 / aSamples[-1]
    nSample = mtxWeight.shape[0] if mtxWeight.ndim == 2 else 1
    # mean TP, FP, FN for each label
    mtxStat = np.zeros((nSample, nLabel*3))
    # p,r,f1 for each label, plus micro+macro
    mtxRslt = np.zeros((nSample, (nLabel+2)*3))
    tpAll, fpAll, fnAll = 0, 0, 0
    for i in range(nLabel):
        tp = np.sum(aSamples[i*3]*mtxWeight, axis=axis)
        fp = np.sum(aSamples[i*3+1]*mtxWeight, axis=axis)
        fn = np.sum(aSamples[i*3+2]*mtxWeight, axis=axis)
        mtxStat[:,i*3], mtxStat[:,i*3+1], mtxStat[:,i*3+2] = tp, fp, fn
        mtxRslt[:,i*3] = tp / (tp + fp)
        mtxRslt[:,i*3+1] = tp / (tp + fn)
        mtxRslt[:,i*3+2] = 2*tp / (2*tp + fp + fn)
        # These are for computing micro metrices
        tpAll += tp
        fpAll += fp
        fnAll += fn

    # Micro stats
    mtxRslt[:,-6] = tpAll / (tpAll + fpAll)
    mtxRslt[:,-5] = tpAll / (tpAll + fnAll)
    mtxRslt[:,-4] = 2*tpAll / (2*tpAll + fpAll + fnAll)

    # Macro stats
    mtxRslt[:,-3] = np.mean(mtxRslt[:,0:-6:3], axis=axis)
    mtxRslt[:,-2] = np.mean(mtxRslt[:,1:-6:3], axis=axis)
    # Macro f1 comes from averaging f1s, instead of using the mean precision and mean recall
    # See J. Opitz; S. Burst (2019). "Macro F1 and Macro F1". arXiv:1911.03347
    mtxRslt[:,-1] = np.mean(mtxRslt[:,2:-6:3], axis=axis)
    if nSample == 1:
        return mtxRslt[0,:]
    else:
        return mtxRslt.transpose()

def main():
    tagOutput = sys.argv.pop(1)
    field = sys.argv[1].strip()
    sys.argv.pop(1)

    sTypesLabel = set()
    aDataRaw = []
    aWeightsInv = []
    for fname in sys.argv[1:]:
        nData = 0
        with open(fname, "r", encoding='utf-8') as fp:
            objReader = csv.DictReader(fp)
            if not field:
                field = objReader.fieldnames[1].removesuffix("-acc")
            for row in objReader:
                nData += 1
                pred = row[F'{field}-pred'].strip()
                aRefs = tuple(row[F'{field}-ref'].strip().split())
                aDataRaw.append((pred, aRefs))
                for label in aRefs:
                    sTypesLabel.add(label)
        for i in range(nData):
            aWeightsInv.append(nData)

    # In the data matrix, each label need 3 values: TP, FP, FN, we'll add weight as the last column
    # If the classification is correct, then TP(ref)=TP(pred)=1
    # If the classification is incorrect, then FN(ref)=1 and FP(pred)=1
    # Shape: (nParameter, nData) as required by scipy.stats.bootstrap
    mSupportLabel = {}
    mTypesLabel = {v: i for i,v in enumerate(sorted(sTypesLabel))}
    mtxData = np.zeros((len(mTypesLabel)*3+1, len(aDataRaw)), dtype=np.int32)
    for i in range(len(aDataRaw)):
        mtxData[-1,i] = aWeightsInv[i]
        pred, aRefs = aDataRaw[i]
        # Convert into indices
        idxPred = mTypesLabel[pred]
        aIdxsRef = tuple(mTypesLabel[v] for v in aRefs)
        if idxPred in aIdxsRef:
            mtxData[idxPred*3,i] = 1
        else:
            mtxData[idxPred*3+1,i] = 1
            for idx in aIdxsRef:
                mtxData[idx*3+2,i] = 1.0 / len(aIdxsRef)
        for idx in aIdxsRef:
            mSupportLabel[idx] = mSupportLabel.get(idx, 0) + 1.0/len(aIdxsRef)

    # Get the empirical value for output
    # The star notation * dieassembles the np.array at the first dimension, so the resulting dimension is (nSample,)
    mean = getClassifierStats(*mtxData)
    print(F"=== Tag {tagOutput} ===", file=sys.stderr)
    print(F"macro-f1 {mean[-1]:.6f} micro-f1 {mean[-4]:.6f}", file=sys.stderr)


    # Actually compute the bootstrap things
    rslt = bootstrap(
            mtxData,
            confidence_level=0.95,
            batch=1000,
            method='basic',
            paired=True,
            statistic=getClassifierStats,
            random_state=np.random.default_rng(),
            )
    #meanBoot = rslt.bootstrap_distribution.mean(axis=-1)
    lower, upper = rslt.confidence_interval
    if (not (mean>lower).all() or not (mean<upper).all()):
        print("Warning: Some empirical values are outside CI, the statistics may be problematic", file=sys.stderr)

    sys.stdout.reconfigure(encoding='utf-8')
    aCols = ['tag', 'support']
    for subfield in ('p', 'r', 'f1'):
        aCols.append(F'{field}-{subfield}')
        aCols.append(F'{field}-{subfield}-95l')
        aCols.append(F'{field}-{subfield}-95u')
    objWriter = csv.DictWriter(sys.stdout, aCols, lineterminator="\n")
    objWriter.writeheader()

    # Per-label output
    print(F"=== Tag {tagOutput} ===", file=sys.stderr)
    for label, i in mTypesLabel.items():
        support = mSupportLabel[i]
        meanF1, lowerF1, upperF1 = mean[i*3+2], lower[i*3+2], upper[i*3+2]
        print(F"{label}({support}): {meanF1:.6f} [{lowerF1:.6f}, {upperF1:.6f}]", file=sys.stderr)
        mOutput = {'tag': F'{tagOutput}-perlabel-{label}', 'support': support}
        mOutput[F'{field}-p'] = mean[i*3]
        mOutput[F'{field}-p-95l'] = lower[i*3]
        mOutput[F'{field}-p-95u'] = upper[i*3]
        mOutput[F'{field}-r'] = mean[i*3+1]
        mOutput[F'{field}-r-95l'] = lower[i*3+1]
        mOutput[F'{field}-r-95u'] = upper[i*3+1]
        mOutput[F'{field}-f1'] = meanF1
        mOutput[F'{field}-f1-95l'] = lowerF1
        mOutput[F'{field}-f1-95u'] = upperF1
        objWriter.writerow(mOutput)

    # Micro statistics
    support = mtxData.shape[1]
    mOutput = {'tag': F'{tagOutput}-micro', 'support': support}
    meanF1, lowerF1, upperF1 = mean[-4], lower[-4], upper[-4]
    print(F"micro({support}): {meanF1:.6f} [{lowerF1:.6f}, {upperF1:.6f}]", file=sys.stderr)
    mOutput[F'{field}-p'] = mean[-6]
    mOutput[F'{field}-p-95l'] = lower[-6]
    mOutput[F'{field}-p-95u'] = upper[-6]
    mOutput[F'{field}-r'] = mean[-5]
    mOutput[F'{field}-r-95l'] = lower[-5]
    mOutput[F'{field}-r-95u'] = upper[-5]
    mOutput[F'{field}-f1'] = meanF1
    mOutput[F'{field}-f1-95l'] = lowerF1
    mOutput[F'{field}-f1-95u'] = upperF1
    objWriter.writerow(mOutput)

    # Macro statistics
    support = len(sTypesLabel)
    mOutput = {'tag': F'{tagOutput}-macro', 'support': support}
    meanF1, lowerF1, upperF1 = mean[-1], lower[-1], upper[-1]
    print(F"macro({support}): {meanF1:.6f} [{lowerF1:.6f}, {upperF1:.6f}]", file=sys.stderr)
    mOutput[F'{field}-p'] = mean[-3]
    mOutput[F'{field}-p-95l'] = lower[-3]
    mOutput[F'{field}-p-95u'] = upper[-3]
    mOutput[F'{field}-r'] = mean[-2]
    mOutput[F'{field}-r-95l'] = lower[-2]
    mOutput[F'{field}-r-95u'] = upper[-1]
    mOutput[F'{field}-f1'] = meanF1
    mOutput[F'{field}-f1-95l'] = lowerF1
    mOutput[F'{field}-f1-95u'] = upperF1
    objWriter.writerow(mOutput)


if __name__ == '__main__':
    main()
