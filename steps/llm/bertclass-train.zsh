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
description="Train a BERT classifier"
dependencies=( "uc/llm/bertclass-train.py" )
importantconfig=( typeModel nameModel )

setupArgs() {
  opt -r out '' "Output BERT"
  optType out output modeldir

  opt -r in '' "Input text"
  optType in input table
  opt -r inLabel '' "Input label"
  optType inLabel input table

  opt typeModel "BERT" "type of HuggingFace Transformer model"
  opt nameModel "bert-base-chinese" "name of HuggingFace base model"
}

main() {
  local outThis
  out::putDir outThis

  in::load \
  | CUDA_VISIBLE_DEVICES=0 uc/llm/bertclass-train.py "$outThis" "$typeModel" "$nameModel" <(inLabel::load)
}

source Mordio/mordio
