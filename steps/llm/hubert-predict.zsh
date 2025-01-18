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
description="Predict output from a HuBERT-based model"
metaDepScripts=("uc/llm/hubert-predict.py")
metaDepOpts=(nbest fieldOutput fieldKey)

setupArgs() {
  opt -r out '' "Output result table"
  optType out output table

  opt -r in '' "Input audio"
  optType in input archive
  opt -r model '' "Input model"
  optType model input modeldir

  opt nbest 5 "Number of nbest to output"
  opt fieldKey 'id' "Name of keys in the resultant table"
  opt fieldOutput 'pred' "Prefix of names of the field of the predictions in the resultant table"
}

main() {
  if ! out::ALL::isReal; then
    err "Unreal table output not supported" 15
  fi

  local nr
  getMeta in 1 nRecord nr

  in::load \
  | MORDIOSCRIPTS_FIELD_OUTPUT=$fieldOutput \
    MORDIOSCRIPTS_FIELD_KEY=$fieldKey \
    uc/llm/hubert-predict.py "$model" "$nbest" \
  | progressBarCsv $nr \
  | out::save
  if [[ $? != 0 ]]; then return 1; fi
}

source Mordio/mordio
