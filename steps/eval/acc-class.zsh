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
description="Compute per-entry accuracy for classification"
dependencies=("uc/eval/acc-class.py")
importantconfig=(fieldOutput fieldRef fieldInput)

setupArgs() {
  opt -r out '' "Output accuracy table"
  optType out output table

  opt -r in '' "Input predict table"
  optType in input table
  opt -r label '' "Input label table"
  optType label input table

  opt fieldOutput 'acc' "Name of the field of the accuracy in the resultant table"
  opt fieldRef '' "Name of reference field. By default the second column"
  opt fieldInput '' "Name of input field. By default the second column"
}

main() {
  local param="$(in::getLoader) | uc/eval/acc-class.py ${(q+)fieldOutput} ${(q+)fieldRef} ${(q+)fieldInput} <($(label::getLoader))"

  if out::isReal; then
    eval "$param" | out::save
    if [[ $? != 0 ]]; then return 1; fi
  else
    echo "$param" | out::save
    if [[ $? != 0 ]]; then return 1; fi
  fi
}

source Mordio/mordio
