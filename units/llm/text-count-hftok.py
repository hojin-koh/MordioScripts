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

# Get token count from a HF-compatible tokenizer
# Usage: text-count-hftok.py <model>

import csv
import sys

from transformers import AutoTokenizer

def main():
    nameModel = sys.argv[1]
    objTok = AutoTokenizer.from_pretrained(nameModel, do_lower_case=False, clean_up_tokenization_spaces=False)

    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    objReader = csv.DictReader(sys.stdin)
    nameKey = objReader.fieldnames[0]
    nameText = objReader.fieldnames[1]
    objWriter = csv.DictWriter(sys.stdout, (nameKey, 'ntoken'), lineterminator="\n")
    objWriter.writeheader()

    for row in objReader:
        key = row[nameKey]
        text = row[nameText].replace("\\n", "\n").strip()
        nTok = len(objTok.encode(text, padding=False, truncation=False))
        objWriter.writerow({nameKey: key, 'ntoken': nTok})
        sys.stdout.flush()

if __name__ == '__main__':
    main()
