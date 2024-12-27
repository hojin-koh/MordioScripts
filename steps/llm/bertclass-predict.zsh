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
description="Predict output from a BERT-based model"
dependencies=("uc/llm/bertclass-predict.py")
importantconfig=(nbest fieldOutput fieldInput)

setupArgs() {
  opt -r out '' "Output result table"
  optType out output table

  opt -r in '' "Input text"
  optType in input table
  opt -r model '' "Input model"
  optType model input modeldir

  opt nbest 5 "Number of nbest to output"
  opt fieldOutput 'pred' "Prefix of names of the field of the predictions in the resultant table"
  opt fieldInput '' "Name of input field. By default the second column"
}

main() {
  if ! out::ALL::isReal; then
    err "Unreal table output not supported" 15
  fi

  local nr
  getMeta in 1 nRecord nr

  in::load \
  | uc/llm/bertclass-predict.py "$fieldOutput" "$fieldInput" "$model" "$nbest" \
  | lineProgressBar $nr \
  | out::save
  if [[ $? != 0 ]]; then return 1; fi
}

source Mordio/mordio
