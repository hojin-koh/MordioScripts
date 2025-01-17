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
description="Do kanji transformations with OpenCC"
metaDepScripts=("uc/text-opencc.py")
metaDepOpts=(config fields)

setupArgs() {
  opt -r out '' "Output text"
  optType out output table

  opt -r in '' "Input text"
  optType in input table

  opt config "s2twp.json" "config name for OpenCC"
  opt fields '' "Which comma-separated fields to transform. By default it will be just 2nd field"
}

main() {
  if ! out::ALL::isReal; then
    err "Unreal table output not supported" 15
  fi

  local nr
  getMeta in 0 nRecord nr

  in::load \
  | uc/text-opencc.py "$config" "$fields" \
  | lineProgressBar $nr \
  | out::save
  if [[ $? != 0 ]]; then return 1; fi
}

source Mordio/mordio
