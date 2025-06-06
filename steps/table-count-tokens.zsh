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
description="Count how many tokens is in the specified field"
metaDepScripts=("uc/table-count-tokens.py")
metaDepOpts=(fieldOutput fieldInput)

setupArgs() {
  opt -r in '' "Input table"
  optType in input table
  opt -r out '' "Output table"
  optType out output table

  opt fieldOutput 'ntoken' "Name of the field of this count in the resultant table"
  opt fieldInput '' "Name of input field. By default the second column"
}

main() {
  local varFields="MORDIOSCRIPTS_FIELD_OUTPUT=${(q+)fieldOutput} "
  varFields+="MORDIOSCRIPTS_FIELD_INPUT=${(q+)fieldInput} "
  local param="$(in::getLoader) | $varFields uc/table-count-tokens.py"
  if out::isReal; then
    eval "$param" | out::save
    if [[ $? != 0 ]]; then return 1; fi
  else
    echo "$param" | out::save
    if [[ $? != 0 ]]; then return 1; fi
  fi
}

source Mordio/mordio
