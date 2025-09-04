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
description="Segment the text document into characters"
metaDepScripts=("uc/text-seg-sent-rough.py")
metaDepOpts=(sep)

setupArgs() {
  opt -r in '' "Input text"
  optType in input table
  opt -r out '' "Output text"
  optType out output table

  opt sep '::sent' "Sentence ID Separator"
}

main() {
  if ! out::ALL::isReal; then
    err "Unreal table output not supported" 15
  fi

  in::load \
  | uc/text-seg-sent-rough.py "$sep" \
  | out::save
  if [[ $? != 0 ]]; then return 1; fi
}

source Mordio/mordio
