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

# Folderize multiple tables into one single table by prefixing/postfixing

import csv
import sys

def main():
    mode = sys.argv[1]
    nameKey = sys.argv[2]

    sys.stdout.reconfigure(encoding='utf-8')
    objWriter = None

    while len(sys.argv) > 3:
        tag = sys.argv[3]
        fname = sys.argv[4]
        sys.argv.pop(4)
        sys.argv.pop(3)
        with open(fname, encoding='utf-8') as fp:
            objReader = csv.DictReader(fp)
            aFields = objReader.fieldnames
            if not objWriter:
                objWriter = csv.DictWriter(sys.stdout, aFields, lineterminator="\n")
                objWriter.writeheader()
            for row in objReader:
                key = row[nameKey]
                aRslt = row
                if mode == 'prefix':
                    aRslt[nameKey] = tag + key
                else:
                    aRslt[nameKey] = key + tag
                objWriter.writerow(aRslt)

if __name__ == '__main__':
    main()
