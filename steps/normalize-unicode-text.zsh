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
description="Normalize unicode in the text"
metaDepScripts=("uc/normalize-unicode.py")
metaDepOpts=(fieldInput)

setupArgs() {
  opt -r out '' "Output text"
  optType out output table

  opt -r in '' "Input text"
  optType in input table
  opt -r conv '' "Input character mapping table"
  optType conv input table

  opt fieldInput '' "Name of input field. By default the second column"
}

main() {
  if ! out::ALL::isReal; then
    err "Unreal table output not supported" 15
  fi

  local nr
  getMeta in 0 nRecord nr
  in::load \
  | MORDIOSCRIPTS_FIELD_INPUT=$fieldInput \
    uc/normalize-unicode.py text <(conv::load) \
  | lineProgressBar $nr \
  | out::save
  if [[ $? != 0 ]]; then return 1; fi
}

source Mordio/mordio
