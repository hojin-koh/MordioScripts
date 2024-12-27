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

# Compute Rouge-1, Rouge-2, and Rouge-L metrics based on a reference text

import csv
import sys

from rouge_metric import PyRouge

def main():
    objRouge = PyRouge(rouge_n=(1, 2), rouge_l=True)
    fileRef = sys.argv[1]

    aTypes = ('rouge-1', 'rouge-2', 'rouge-l')
    mRef = {}
    with open(fileRef, "r", encoding='utf-8') as fp:
        objReader = csv.DictReader(fp)
        nameKey = objReader.fieldnames[0]
        nameRef = objReader.fieldnames[1]
        for row in objReader:
            mRef[row[nameKey]] = row[nameRef].replace("\\n", "\n").strip()

    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    objReader = csv.DictReader(sys.stdin)
    nameKey = objReader.fieldnames[0]
    nameText = objReader.fieldnames[1]
    aCols = [nameKey]
    for typ in ('rs1', 'rs2', 'rsl'):
        aCols.append(F'{typ}-p')
        aCols.append(F'{typ}-r')
        aCols.append(F'{typ}-f1')
    objWriter = csv.DictWriter(sys.stdout, aCols, lineterminator="\n")
    objWriter.writeheader()

    for row in objReader:
        key = row[nameKey]
        text = row[nameText].replace("\\n", "\n").strip()
        # The cursed brackets are because this library expects hyp to be in a list, and ref in a list of lists (to support multiple references)
        mRouge = objRouge.evaluate([text], [[mRef[key]]])
        mRslt = {nameKey: key}
        for typ, typLib in (('rs1', 'rouge-1'), ('rs2', 'rouge-2'), ('rsl', 'rouge-l')):
            mRslt[F'{typ}-p'] = mRouge[typLib]['p']
            mRslt[F'{typ}-r'] = mRouge[typLib]['r']
            mRslt[F'{typ}-f1'] = mRouge[typLib]['f']
        objWriter.writerow(mRslt)
        sys.stdout.flush()

if __name__ == '__main__':
    main()
