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
description="Filter an archive through other tables and a python expression"
metaDepScripts=("uc/archive-filter.py")
metaDepOpts=(filt omitAbsentKeys)

setupArgs() {
  opt -r out '' "Output archive"
  optType out output archive

  opt -r in '' "Input archive"
  optType in input archive
  opt -r infilt '()' "Filter table"
  optType infilt input table

  opt filt '1 == 1' "Filter expression in python, like record['grade'] >= 5 and record['ntoken'] < 3000"
  opt omitAbsentKeys true "Whether to omit keys from output that don't exist in filter tables"
}

main() {
  local param="$(in::getLoader) | uc/archive-filter.py"
  if [[ $omitAbsentKeys == true ]]; then
    param+=" --omit-absent-keys"
  fi
  param+=" ${(q+)filt}"
  
  local i
  for (( i=1; i<=$#infilt; i++ )); do
    param+=" <($(infilt::getLoader $i))"
  done

  if out::isReal; then
    eval "$param" | out::save
    if [[ $? != 0 ]]; then return 1; fi
  else
    echo "$param" | out::save
    if [[ $? != 0 ]]; then return 1; fi
  fi
}

source Mordio/mordio
