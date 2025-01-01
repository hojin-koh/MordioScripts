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
metaDepScripts=("uc/dataset-cv-split.py")
metaDepOpts=(fieldOutput fieldLabel fieldGroup)

setupArgs() {
  opt -r in '' "Input label table"
  optType in input table
  opt -r out '()' "Output key table"
  optType out output table

  opt inGroup '' "Input group table"
  optType inGroup input table

  opt fieldOutput 'set' "Name of the field of the set name in the resultant tables"
  opt fieldLabel '' "Name of reference field. By default the second column"
  opt fieldGroup '' "Name of group field for adversial splitting. By default the second column"
}

main() {
  if ! out::ALL::isReal; then
    err "Unreal table output not supported" 15
  fi

  local nSplit=$#out
  info "nSplit = $nSplit"

  local dirTemp
  putTemp dirTemp

  local varFields="MORDIOSCRIPTS_FIELD_OUTPUT=${(q+)fieldOutput} "
  varFields+="MORDIOSCRIPTS_FIELD_LABEL=${(q+)fieldLabel} "
  varFields+="MORDIOSCRIPTS_FIELD_GROUP=${(q+)fieldGroup} "
  local param="$(in::getLoader) | $varFields uc/dataset-cv-split.py"
  # TODO: Adversial mode
  if [[ -n $inGroup ]]; then
    true
  fi

  for (( i=1; i<=$nSplit; i++ )); do
    mkfifo $dirTemp/$i.pipe
    param+=" $dirTemp/$i.pipe"
  done
  eval "$param" &

  for (( i=1; i<=$nSplit; i++ )); do
    cat $dirTemp/$i.pipe \
    | out::save $i
    if [[ $? != 0 ]]; then return 1; fi
  done
  wait
}

source Mordio/mordio
