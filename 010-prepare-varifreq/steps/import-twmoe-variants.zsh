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
description="Import twmoe variants table from https://github.com/kcwu/moedict-variants"
dependencies=("us/parse-variants-confusables.py")
importantconfig=()

setupArgs() {
  opt -r out '' "Output table"
  optType out output table

  opt -r in '' "Original Data File"
  opt -r confusable '' "ICU's confusable table"
  opt -r infreq '' "Input character frequency table"
  optType infreq input table
}

main() {
  if [[ ! -f "$in" ]]; then
    info "Downloading the variants data from github.com ..."
    # Backup: https://web.archive.org/web/20240602054933/https://raw.githubusercontent.com/kcwu/moedict-variants/master/list.txt
    curl -L -o "$in" 'https://raw.githubusercontent.com/kcwu/moedict-variants/master/list.txt'
  fi

  if [[ ! -f "$confusable" ]]; then
    info "Downloading the ICU confusable data 2024-08-20 from github.com ..."
    curl -L -o "$confusable" 'https://github.com/unicode-org/icu/raw/51e21af692e95737ad8f75fdf2dbf105fe5811b0/icu4c/source/data/unidata/confusables.txt'
  fi

  if ! out::isReal; then
    err "Unreal table output not supported" 15
  fi

  if [[ "$in" == *.txt ]]; then # Github version
    us/parse-variants-confusables.py "$confusable" <(infreq::load) < "$in" \
    | out::save
  else # old dump version found on the internet https://mega.nz/file/lVAAhR4T#qE9JLx4mhfjHe_Zni_lahPUK2qc5c394_v973PuN28k
    # This version will give you a very long and noisy table
    tar xOf "$in" \
    | us/parse-variants-confusables.py --old "$confusable" <(infreq::load) \
    | out::save
  fi
  return $?
}

source Mordio/mordio
