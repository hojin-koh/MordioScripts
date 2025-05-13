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
description="Extract embedding from a HuBERT-based model"
metaDepScripts=("uc/llm/hubert-embed.py")
metaDepOpts=()

setupArgs() {
  opt -r out '' "Output result archive"
  optType out output archive

  opt -r in '' "Input audio"
  optType in input archive
  opt -r model '' "Input model"
  optType model input modeldir
}

main() {
  if ! out::ALL::isReal; then
    err "Unreal archive output not supported" 15
  fi

  local nr
  getMeta in 1 nRecord nr

  in::load \
  | uc/llm/hubert-embed.py "$model" \
  | progressBarTar $nr \
  | out::save
  if [[ $? != 0 ]]; then return 1; fi
}

source Mordio/mordio
