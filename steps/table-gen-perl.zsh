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
description="Generate a new table based on another table with a perl conversion rule"
metaDepScripts=()
metaDepOpts=(header rule)

setupArgs() {
  opt -r out '' "Output table"
  optType out output table

  opt -r header '' "Table header of the new table"
  opt -r rule '' "Perl conversion rule"
  opt -r in '' "Input table"
  optType in input table
}

main() {
  info "Header: $header"
  info "ID conversion rule: $rule"

  local param="echo ${(q+)header}; $(in::getLoader) | tail +2 | perl -CSAD -nle ${(q+)rule}"
  if out::isReal; then
    eval "$param" | out::save
    if [[ $? != 0 ]]; then return 1; fi
  else
    echo "$param" | out::save
    if [[ $? != 0 ]]; then return 1; fi
  fi
}

source Mordio/mordio
