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
description="Sort a table through other tables"
dependencies=("uc/table-sort.py")
importantconfig=(nameSortKey nameKey doNumSort directionSort)

setupArgs() {
  opt -r out '' "Output table"
  optType out output table

  opt -r in '' "Input table"
  optType in input table
  opt -r inbase '()' "Data table"
  optType inbase input table
  opt -r nameSortKey '' "Name of the key the sorting based on"

  opt nameKey 'id' "Name of the column containing keys for sorting"
  opt doNumSort false "Whether to do numeric sorting"
  opt directionSort 'asc' "Either desc or asc"
}

main() {
  if [[ $directionSort != asc && $directionSort != desc ]]; then
    err "directionSort must be either 'asc' or 'desc'" 15
  fi

  local param="$(in::getLoader) | uc/table-sort.py"
  if [[ $doNumSort == true ]]; then
    param+=" --do-num-sort"
  fi
  param+=" '$nameKey' '$nameSortKey' '$directionSort'"
  
  local i
  for (( i=1; i<=$#inbase; i++ )); do
    param+=" <($(inbase::getLoader $i))"
  done

  if out::isReal $i; then
    eval "$param" | out::save $i
    if [[ $? != 0 ]]; then return 1; fi
  else
    echo "$param" | out::save $i
    if [[ $? != 0 ]]; then return 1; fi
  fi
}

source Mordio/mordio
