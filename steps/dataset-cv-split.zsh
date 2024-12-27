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
description="Get all the dataset split spec for cross-validation"
dependencies=("uc/dataset-cv-split.py")
importantconfig=(nSplit)

setupArgs() {
  opt -r in '' "Input label table"
  optType in input table
  opt -r out '()' "Output key table"
  optType out output table

  opt -r nSplit '' "Number of splits"
}

main() {
  if ! out::ALL::isReal; then
    err "Unreal table output not supported" 15
  fi

  if [[ $#out != $nSplit ]]; then
    err "In this configuration, there must be exactly $nSplit output tables" 15
  fi

  # TODO: faster, only 1 call
  for (( i=1; i<=$nSplit; i++ )); do
    in::load \
    | uc/dataset-cv-split.py "$nSplit" $[i-1] \
    | out::save $i
    if [[ $? != 0 ]]; then return 1; fi
  done
}

source Mordio/mordio
