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
description="Generate a new table from content entered on the command line"
metaDepScripts=()
metaDepOpts=(header data)

setupArgs() {
  opt -r out '' "Output table"
  optType out output table

  opt -r header '' "Table header of the new table"
  opt -r data '()' "Data lines"
}

main() {
  if ! out::ALL::isReal; then
    err "Unreal table output not supported" 15
  fi

  info "Header: $header"
  local line
  (
    echo "$header";
    for line in "${data[@]}"; do
      printf '%s\n' "$line"
    done
  ) \
  | out::save
}

source Mordio/mordio
