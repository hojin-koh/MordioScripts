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

# Parse twmoe variants table, supposedly from https://github.com/kcwu/moedict-variants
# Need two additional files:
#   sys.argv[1] ICU confusable.txt
#   sys.argv[2] character frequency table for tie-breaking

import csv
import fileinput
import re
import sys
import unicodedata

from opencc import OpenCC


def main():
    modeOld = False
    if sys.argv[1] == "--old":
        modeOld = True
        sys.argv.pop(1)

    objOpenCC = OpenCC('s2tw.json')

    # Read ICU confusable table
    mConfusable = {}
    for line in fileinput.input(sys.argv[1], encoding='utf-8'):
        line = line.strip()
        # Don't touch Japanese texts
        if line.find("KATAKANA") != -1 or line.find("HIRAGANA") != -1:
            continue

        match = re.search(R'\(\s*(\S)\s*→\s*(\S)\s*\)', line)
        if match:
            c1 = unicodedata.normalize('NFKC', match.group(1))
            c2 = unicodedata.normalize('NFKC', match.group(2))
            if c1 == c2:
                continue

            # Non-letters (symbols, punctuations, etc)
            if unicodedata.category(c2)[0] != 'L':
                continue

            # Not a wide character... likely not what we're interested in
            if unicodedata.east_asian_width(c2) != 'W':
                continue

            mConfusable[c1] = c2

    # Read character frequency table
    mFreq = {}
    with open(sys.argv[2], encoding='utf-8') as fp:
        objReader = csv.DictReader(fp)
        for row in objReader:
            mFreq[row['char']] = int(row['freq'])

    # Read the real deal
    sys.stdin.reconfigure(encoding='utf-8')
    mGoodChar = {} # The main good chars table
    mCharId = {} # The reverse table of each good chars
    mVar = {} # Variants
    mVarId = {} # The reverse table of each variant chars
    for line in sys.stdin:
        if modeOld:
            dumb, line = line.split('\t', 1)
            if len(line.strip()) == 0: continue

            match = re.search(R'"row">(附 錄 字|異 體 字|正 字).*<code>([-A-Z0-9]+)</code>.*<big2>(?:<img alt=")?([^"<]+)["<]', line.strip())
            cid = match.group(2)
            if match.group(1) == "正 字":
                tag = '正'
            else:
                tag = '異'

            c = match.group(3)
            # Filter out non-standard custom characters and weird catches
            if len(c) != 1: continue
            if unicodedata.category(c) == 'Co':
                continue
            c = unicodedata.normalize('NFKC', c)
        else:
            cid, tag, dumb, c, dumb = line.split('\t')

            # Filter out non-standard custom characters and weird catches
            if len(c) != 1: continue
            if unicodedata.category(c) == 'Co':
                continue
            c = unicodedata.normalize('NFKC', c)

        if c not in mVarId:
            mVarId[c] = []
        mVar[cid] = c

        if tag == '正':
            # For duplicated chars, create a link
            if c in mCharId:
                mGoodChar[cid] = mGoodChar[mCharId[c]]
                continue
            mGoodChar[cid] = {
                    'variants': [c],
                    'char': c,
                    'freq': mFreq.get(c, 0),
                    }
            mCharId[c] = cid
            mVarId[c].append(cid)

    # Step 10: build missing good chars with lowest-numbered variant
    for cid in sorted(mVar):
        cidGood = cid.split('-')[0]
        c = mVar[cid]
        if c in mCharId: continue
        if cidGood in mGoodChar: continue
        mGoodChar[cidGood] = {
                'variants': [c],
                'char': c,
                'freq': mFreq.get(c, 0),
                }
        mCharId[c] = cidGood

    # Step 20: Put ICU confusable chars into the mix
    numICU = 0
    for c1, c2 in mConfusable.items():
        numICU += 1
        # The "target" char is considered the good char
        if c2 not in mCharId:
            idICU = F'ICU{numICU:05d}'
            mCharId[c2] = idICU
            mGoodChar[idICU] = {
                    'char': c2,
                    'freq': mFreq.get(c2, 0),
                    'variants': [c2],
                    }
        else:
            idICU = mCharId[c2]

        # The "source" char is considered a variant of the "target" char
        if c2 not in mVarId:
            mVarId[c2] = [idICU]
        if c1 not in mVarId:
            mVarId[c1] = []
        idICUVar = F'{idICU}-999'
        mVar[idICUVar] = c1

    # Step 30: file all variants into GoodChars table
    for cid in sorted(mVar):
        cidGood = cid.split('-')[0]
        c = mVar[cid]
        # At this point, if there's still no good chars, ignore it
        if cidGood not in mGoodChar:
            continue

        # If it is already there, ignore it
        if c in mGoodChar[cidGood]['variants']:
            continue

        # If it is also a good char, but is a class-C char (rarely-used)
        # And it can also be classified as a variant of class-A or class-B char
        # Then delete that class-C char to avoid problems
        if c in mCharId and not cid.startswith("C") and mCharId[c].startswith("C"):
            del mGoodChar[mCharId[c]]
            del mCharId[c]

        # If it is also a normal good char, ignore it
        if c in mCharId:
            continue

        # Add it
        mGoodChar[cidGood]['variants'].append(c)
        mVarId[c].append(cidGood)

    # Step 110: Dedup variants
    for v, aCid in tuple(mVarId.items()):
        # Check if this good char was deleted in the last step
        for cid in aCid:
            if cid not in mGoodChar:
                aCid.remove(cid)
        if len(aCid) <= 1: continue
        # First, see if said character is a simplified version of another char
        # If there's none, then decide by word frequency
        vTrad = objOpenCC.convert(v)
        cidKeep = max(aCid, key=lambda cid: int(mGoodChar[cid]['char'] == vTrad and not cid.startswith("c"))*10000000 + mGoodChar[cid]['freq'])
        for cid in aCid:
            if cid == cidKeep: continue
            mGoodChar[cid]['variants'].remove(v)
            mVarId[v].remove(cid)

    # Step 130: delete all good chars that actually has no variants
    for cid in sorted(mGoodChar):
        if len(mGoodChar[cid]['variants']) > 1: continue
        c = mGoodChar[cid]['char']
        if c in mCharId:
            del mCharId[c]
        del mGoodChar[cid]

    # Step 210: Change the good char if it can be converted to traditional chinese which match one of its variants
    # (Will probably break mCharId here)
    for cid, m in mGoodChar.items():
        if len(m['variants']) <= 1: continue
        charOrig = m['char']
        charNew = objOpenCC.convert(charOrig)
        if charOrig != charNew and charNew in m['variants']:
            m['char'] = charNew

    # Finally, print! and skip empty good chars
    sys.stdout.reconfigure(encoding='utf-8')
    objWriter = csv.DictWriter(sys.stdout, ('before', 'after'), lineterminator="\n")
    objWriter.writeheader()

    for key in sorted(mGoodChar):
        m = mGoodChar[key]
        if len(m['variants']) <= 1: continue
        c2 = m['char']
        for c1 in m['variants']:
            if c1 == c2: continue
            objWriter.writerow({'before': c1, 'after': c2})

    # Hard-coded characters
    objWriter.writerow({'before': "臺", 'after': "台"})
    objWriter.writerow({'before': "萠", 'after': "萌"})
    objWriter.writerow({'before': "畅", 'after': "暢"})
    objWriter.writerow({'before': "𣈱", 'after': "暢"})
    objWriter.writerow({'before': "𠚕", 'after': "齒"})

    # There are from OpenCC
    objWriter.writerow({'before': "啓", 'after': "啟"})
    objWriter.writerow({'before': "喫", 'after': "吃"})
    objWriter.writerow({'before': "幺", 'after': "么"})
    objWriter.writerow({'before': "棱", 'after': "稜"})
    objWriter.writerow({'before': "檐", 'after': "簷"})
    objWriter.writerow({'before': "泄", 'after': "洩"})
    objWriter.writerow({'before': "痹", 'after': "痺"})
    objWriter.writerow({'before': "皁", 'after': "皂"})
    objWriter.writerow({'before': "睾", 'after': "睪"})
    objWriter.writerow({'before': "祕", 'after': "秘"})
    objWriter.writerow({'before': "纔", 'after': "才"})
    objWriter.writerow({'before': "脣", 'after': "唇"})
    objWriter.writerow({'before': "蔘", 'after': "參"})
    objWriter.writerow({'before': "覈", 'after': "核"})
    objWriter.writerow({'before': "踊", 'after': "踴"})
    objWriter.writerow({'before': "鍼", 'after': "針"})
    objWriter.writerow({'before': "齶", 'after': "顎"})
    # Reversed OpenCC
    objWriter.writerow({'before': "汙", 'after': "污"})

if __name__ == '__main__':
    main()
