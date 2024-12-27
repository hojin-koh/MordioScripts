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
description="Compute mean and bootstrapped 95% confidence interval for some statistics"
metaDepScripts=("uc/eval/mean-boot.py")
metaDepOpts=(mode tag fields)

setupArgs() {
  opt -r out '' "Output result table"
  optType out output table

  opt -r in '()' "Input stats table"
  optType in input table

  opt -r mode '' "CV/mean"
  opt -r tag '()' "Tag used for each input file in mean mode, or the overall tag for CV mode"
  opt fields '' "Comma-separated fields to be processed, all of omitted"
}

main() {
  if [[ $mode == CV ]]; then
    local param=""
    local i
    for (( i=1; i<=$#in; i++ )); do
      param+=" <($(in::getLoader $i))"
    done
    eval "uc/eval/mean-boot.py "$fields" ${tag[1]} $param" \
    | out::save
    if [[ $? != 0 ]]; then return 1; fi
  elif [[ $mode == mean ]]; then
    if [[ $#in != $#tag ]]; then
      err 'In mean mode, argument tag and in should have same length' 15
    fi
    err "Not implemented yet" 15
    if [[ $? != 0 ]]; then return 1; fi
  fi
}

source Mordio/mordio
