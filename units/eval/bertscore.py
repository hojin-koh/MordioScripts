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

# Calculate BERTScore based on a reference text

import csv
import sys

from bert_score import BERTScorer

def main():
    objBERTScore = BERTScorer(lang=sys.argv[1], rescale_with_baseline=False)
    fileRef = sys.argv[2]

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
    objWriter = csv.DictWriter(sys.stdout, (nameKey, 'bs-p', 'bs-r', 'bs-f1'), lineterminator="\n")
    objWriter.writeheader()

    for row in objReader:
        key = row[nameKey]
        text = row[nameText].replace("\\n", "\n").strip()
        # The cursed brackets are because this library expects hyp to be in a list, and ref in a list of lists (to support multiple references)
        p, r, f = objBERTScore.score([text], [[mRef[key]]])
        objWriter.writerow({nameKey: key, 'bs-p': p.item(), 'bs-r': r.item(), 'bs-f1': f.item()})
        sys.stdout.flush()

if __name__ == '__main__':
    main()
