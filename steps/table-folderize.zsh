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
description="Folderize multiple tables into one table by prefixing/postfixing tag"
dependencies=("uc/table-folderize.py")
importantconfig=(tag nameKey mode)

setupArgs() {
  opt -r out '' "Output table"
  optType out output table

  opt -r tag '()' "Tags for prefix/postfix in the corresponding table"
  opt -r in '()' "Input tables"
  optType in input table

  opt nameKey 'id' "Name of the column containing keys for filtering"
  opt mode 'prefix' "prefix/postfix"
}

main() {
  if [[ $#tag != $#in ]]; then
    err 'Argument tag and in should have same length' 15
  fi

  local param="uc/table-folderize.py ${(q+)mode} ${(q+)nameKey}"
  local i
  for (( i=1; i<=$#tag; i++ )); do
    param+=" ${(q+)tag[$i]} <($(in::getLoader $i))"
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
