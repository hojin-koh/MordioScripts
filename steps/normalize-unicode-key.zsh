#!/usr/bin/env zsh
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
description="Normalize unicode in the keys of a table"
dependencies=( "uc/normalize-unicode.py" "uc/table-interpolate.py" ) # "uc/table-merge.py" 
importantconfig=(mode)

setupArgs() {
  opt -r out '' "Output table"
  optType out output table

  opt -r in '' "Input table"
  optType in input table
  opt -r conv '' "Input character mapping table"
  optType conv input table

  opt mode 'merge' "How to deal with duplicated keys, merge or interpolate"
}

main() {
  if ! out::ALL::isReal; then
    err "Unreal table output not supported" 15
  fi

  # TODO: uc/table-merge.py --set
  in::load \
  | uc/normalize-unicode.py <(conv::load) key \
  | if [[ $mode == merge ]]; then err "Not implemented" 12; else uc/table-interpolate.py 1.0 /dev/stdin; fi \
  | out::save
  if [[ $? != 0 ]]; then return 1; fi
}

source Mordio/mordio
