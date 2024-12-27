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
import os
import sys

from rouge_metric import PyRouge

def main():
    fieldOutput = os.environ.get('MORDIOSCRIPTS_FIELD_OUTPUT', 'rs')
    fieldRef = os.environ.get('MORDIOSCRIPTS_FIELD_LABEL', '')
    fieldInput = os.environ.get('MORDIOSCRIPTS_FIELD_TEXT', '')

    fileRef = sys.argv.pop(1)
    objRouge = PyRouge(rouge_n=(1, 2), rouge_l=True)

    aTypes = ('rouge-1', 'rouge-2', 'rouge-l')
    mRef = {}
    with open(fileRef, "r", encoding='utf-8') as fp:
        objReader = csv.DictReader(fp)
        fieldKey = objReader.fieldnames[0]
        if not fieldRef:
            fieldRef = objReader.fieldnames[1]
        for row in objReader:
            mRef[row[fieldKey]] = row[fieldRef].replace("\\n", "\n").strip()

    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    objReader = csv.DictReader(sys.stdin)
    fieldKey = objReader.fieldnames[0]
    if not fieldInput:
        fieldInput = objReader.fieldnames[1]
    aCols = [fieldKey]
    for typ in (F'{fieldOutput}1', F'{fieldOutput}2', F'{fieldOutput}l'):
        aCols.append(F'{typ}-p')
        aCols.append(F'{typ}-r')
        aCols.append(F'{typ}-f1')
    objWriter = csv.DictWriter(sys.stdout, aCols, lineterminator="\n")
    objWriter.writeheader()

    for row in objReader:
        key = row[fieldKey]
        text = row[fieldInput].replace("\\n", "\n").strip()
        # The cursed brackets are because this library expects hyp to be in a list, and ref in a list of lists (to support multiple references)
        mRouge = objRouge.evaluate([text], [[mRef[key]]])
        mRslt = {fieldKey: key}
        for typ, typLib in ((F'{fieldOutput}1', 'rouge-1'), (F'{fieldOutput}2', 'rouge-2'), (F'{fieldOutput}l', 'rouge-l')):
            mRslt[F'{typ}-p'] = mRouge[typLib]['p']
            mRslt[F'{typ}-r'] = mRouge[typLib]['r']
            mRslt[F'{typ}-f1'] = mRouge[typLib]['f']
        objWriter.writerow(mRslt)
        sys.stdout.flush()

if __name__ == '__main__':
    main()
