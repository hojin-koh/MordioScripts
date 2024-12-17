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

# Count how many space-separated tokens are in the second field (whatever its name)

import csv
import re
import sys

def main():
    nameOutput = sys.argv[1]

    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    objReader = csv.DictReader(sys.stdin)
    nameKey = objReader.fieldnames[0]
    nameText = objReader.fieldnames[1]
    objWriter = csv.DictWriter(sys.stdout, (nameKey, nameOutput), lineterminator="\n")
    objWriter.writeheader()

    for row in objReader:
        key = row[nameKey]
        cnt = len(row[nameText].replace("\\n", "\n").strip().split())
        objWriter.writerow({nameKey: key, nameOutput: cnt})

if __name__ == '__main__':
    main()
