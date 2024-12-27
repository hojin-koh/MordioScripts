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
description="Import google chinese character frequency table from google n-gram at https://storage.googleapis.com/books/ngrams/books/datasetsv3.html"
metaDepScripts=("us/parse-google-charfreq.py")
metaDepOpts=()

setupArgs() {
  opt -r out '' "Output table"
  optType out output table
  opt -r in '' "Original Data Archive"
}

main() {
  if [[ ! -f "$in" ]]; then
    info "Downloading the data from google ..."
    curl -L -o "$in" 'http://storage.googleapis.com/books/ngrams/books/20200217/chi_sim/1-00000-of-00001.gz'
  fi

  if ! out::isReal; then
    err "Unreal table output not supported" 15
  fi

  (
    echo "char,freq";
    gunzip -c "$in" \
    | perl -CSAD -nle 'print if /^\p{Han}\t/' \
    | us/parse-google-charfreq.py \
    | sort -k2,2 -nr
  ) \
  | out::save
  return $?
}

source Mordio/mordio
