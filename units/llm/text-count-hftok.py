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
import os
import sys

from transformers import AutoTokenizer

def main():
    fieldOutput = os.environ.get('MORDIOSCRIPTS_FIELD_OUTPUT', 'ntoken')
    fieldInput = os.environ.get('MORDIOSCRIPTS_FIELD_TEXT', '')
    nameModel = sys.argv.pop(1)
    objTok = AutoTokenizer.from_pretrained(nameModel, do_lower_case=False, clean_up_tokenization_spaces=False)

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
        text = row[fieldInput].replace("\\n", "\n").strip()
        nTok = len(objTok.encode(text, padding=False, truncation=False))
        objWriter.writerow({fieldKey: key, 'ntoken': nTok})
        sys.stdout.flush()

if __name__ == '__main__':
    main()
