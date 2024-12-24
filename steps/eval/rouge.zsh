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
description="Compute ROUGE-{1,2,L} scores"
dependencies=("uc/eval/rouge.py")
importantconfig=()

setupArgs() {
  opt -r in '' "Input text"
  optType in input table
  opt -r ref '' "Reference text"
  optType ref input table
  opt -r out '' "Output table"
  optType out output table
}

main() {
  if ! out::ALL::isReal; then
    err "Unreal table output not supported" 15
  fi

  local dirTemp
  putTemp dirTemp

  local nr
  getMeta in 0 nRecord nr

  # ROUGE is a bit slow, and we expect evaluations to run fast
  if [[ $nr -lt 3000 ]]; then
    in::load \
    | processSub \
    | lineProgressBar $nr \
    | out::save
    if [[ $? != 0 ]]; then return 1; fi
  else
    # Get a list of all text
    in::loadKey > "$dirTemp/all.list"
    in::load \
    | doParallelPipeText "$nj" "$nr" "$dirTemp/all.list" \
    "$dirTemp" \
    "processSub" \
    | out::save
    if [[ $? != 0 ]]; then return 1; fi
  fi
}

processSub() {
  uc/eval/rouge.py <(ref::load)
}

source Mordio/mordio
