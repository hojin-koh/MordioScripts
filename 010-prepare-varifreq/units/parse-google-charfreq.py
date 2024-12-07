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

# Parse google chinese n-gram, filtered from https://storage.googleapis.com/books/ngrams/books/datasetsv3.html

import fileinput

from opencc import OpenCC

def main():
    objOpenCC = OpenCC('s2tw.json')

    aOrder = []
    mCount = {}
    for line in fileinput.input():
        c, strRecords = line.strip().split('\t', 1)
        c = objOpenCC.convert(c)
        countThis = sum(int(rec.split(',')[1]) for rec in strRecords.split('\t'))
        aOrder.append(c)
        mCount[c] = mCount.get(c, 0) + countThis

    for c in aOrder:
        print(F'{c},{mCount[c]}')

if __name__ == '__main__':
    main()
