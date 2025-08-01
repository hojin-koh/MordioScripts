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

from fast_bleu import BLEU

def main():
    fieldOutput = os.environ.get('MORDIOSCRIPTS_FIELD_OUTPUT', 'rs')
    fieldRef = os.environ.get('MORDIOSCRIPTS_FIELD_LABEL', '')
    fieldInput = os.environ.get('MORDIOSCRIPTS_FIELD_TEXT', '')

    fileRef = sys.argv.pop(1)

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
    objWriter = csv.DictWriter(sys.stdout, (fieldKey, fieldOutput), lineterminator="\n")
    objWriter.writeheader()

    for row in objReader:
        key = row[fieldKey]
        aHyp = row[fieldInput].replace("\\n", "\n").strip().split()
        aRef = mRef[key].split()
        # The extra bracket are because this library expects ref and hyp to be in a list
        objBleu = BLEU([aRef], {'4gram': (1/4.,1/4.,1/4.,1/4.)})
        mBleu = objBleu.get_score([aHyp])

        objWriter.writerow({fieldKey: key, fieldOutput: mBleu['4gram'][0]})
        sys.stdout.flush()

if __name__ == '__main__':
    main()
