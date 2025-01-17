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
description="Compute bootstrapped 95% confidence interval for multiclass classification results"
metaDepScripts=("uc/eval/boot-class.py")
metaDepOpts=(tag field)

setupArgs() {
  opt -r out '' "Output result table"
  optType out output table

  opt -r in '()' "Input stats table, will assume CV mode of equal weight if there are multiple"
  optType in input table

  opt -r tag '' "Tag used for output"
  opt field '' "The input field to be processed, will infer from input if omitted"
}

main() {
  local param=""
  local i
  for (( i=1; i<=$#in; i++ )); do
    param+=" <($(in::getLoader $i))"
  done
  eval "uc/eval/boot-class.py ${(q+)field} ${(q+)tag} $param" \
  | out::save
  if [[ $? != 0 ]]; then return 1; fi
}

source Mordio/mordio
