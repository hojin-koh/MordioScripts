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
description="Do arithmetics with fields with multiple tables"
metaDepScripts=("uc/table-arith.py")
metaDepOpts=(omitAbsentKeys field arith)

setupArgs() {
  opt -r out '' "Output table"
  optType out output table

  opt -r in '' "Input table"
  optType in input table
  opt -r indata '()' "Data input tables"
  optType indata input table

  opt -r field '()' "Name of output fields"
  opt -r arith '()' "Python arithemetic expression, like data['grade'][0] + max(data['ntoken'])"
  opt omitAbsentKeys true "Whether to silently omit keys from output that don't exist in data tables"
}

main() {
  if [[ $#field != $#arith ]]; then
    err 'Argument field and arith should have same length' 15
  fi

  local param="$(in::getLoader) | uc/table-arith.py"
  if [[ $omitAbsentKeys == true ]]; then
    param+=" --omit-absent-keys"
  fi

  local i
  for (( i=1; i<=$#indata; i++ )); do
    param+=" <($(indata::getLoader $i))"
  done
  param+=" --"

  for (( i=1; i<=$#field; i++ )); do
    param+=" ${(q+)field[$i]} ${(q+)arith[$i]}"
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
