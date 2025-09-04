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

# Segment text into sentences

import csv
import re
import sys

def main():
    sepKey = sys.argv.pop(1)

    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    objReader = csv.DictReader(sys.stdin)
    fieldKey = objReader.fieldnames[0]
    fieldText = objReader.fieldnames[1]

    objWriter = csv.DictWriter(sys.stdout, (fieldKey, fieldText), lineterminator="\n")
    objWriter.writeheader()

    for i, row in enumerate(objReader):
        key = row[fieldKey]
        text = row[fieldText].replace("\\n", "\n").strip()
        aSplits = re.split(R'([。！？；：\.!?:;．]+\s*)', text)
        aSents = [aSplits[i] + (aSplits[i+1] if i+1 < len(aSplits) else "")
                  for i in range(0, len(aSplits), 2)]
        # Sanity check
        if len(aSents) == 0:
            print(F"Warning: No sentences in row {i+1}", file=sys.stderr)
        for idSent, sent in enumerate(aSents):
            if len(sent.strip()) == 0:
                continue
            objWriter.writerow({fieldKey: F"{key}{sepKey}{idSent+1:05d}", fieldText: sent.strip()})
        sys.stdout.flush()

if __name__ == '__main__':
    main()
