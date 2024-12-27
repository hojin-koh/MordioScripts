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

# Do chinese text conversion with OpenCC

import csv
import sys

import opencc

def main():
    nameConfig = sys.argv.pop(1)
    aFields = [field for field in sys.argv.pop(1).strip().split(',') if len(field) > 0]
    objConv = opencc.OpenCC(nameConfig)

    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    objReader = csv.DictReader(sys.stdin)
    if len(aFields) == 0:
        aFields.append(objReader.fieldnames[1])
    objWriter = csv.DictWriter(sys.stdout, objReader.fieldnames, lineterminator="\n")
    objWriter.writeheader()

    for row in objReader:
        for field in aFields:
            text = row[field].replace("\\n", "\n").strip()
            textNew = objConv.convert(text).replace("\n", "\\n")
            row[field] = textNew
        objWriter.writerow(row)
        sys.stdout.flush()

if __name__ == '__main__':
    main()
