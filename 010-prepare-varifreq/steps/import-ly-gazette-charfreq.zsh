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
description="Import Taiwanese parliment charfreq data"
metaDepScripts=()
metaDepOpts=()

setupArgs() {
  opt -r out '' "Output table"
  optType out output table
  opt -r in '' "Original TSV file"
}

main() {
  if [[ ! -f "$in" ]]; then
    info "Downloading the data from gist ..."
    # Backup: https://web.archive.org/web/20241207030627/https://gist.githubusercontent.com/gugod/4361804/raw/7fea308a3990d6ff72ad9337f5763ec6016a6394/ly-gazette-character-frequency.tsv
    curl -L -o "$in" 'https://gist.github.com/gugod/4361804/raw/7fea308a3990d6ff72ad9337f5763ec6016a6394/ly-gazette-character-frequency.tsv'
  fi

  if ! out::isReal; then
    err "Unreal table output not supported" 15
  fi

  (
    echo "char,freq";
    cat "$in" \
    | perl -CSAD -lpe 's/\s+/,/g'
  ) \
  | out::save
  return $?
}

source Mordio/mordio
