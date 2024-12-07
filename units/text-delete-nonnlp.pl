#!/usr/bin/env perl
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

# Filter out non-word things which are useless in NLP tasks
# Input is in "doc_id,content" format
# If there is no comma in the line, then we assume that document is empty, and just output the original id

use strict;
use warnings;
use utf8;
use open qw(:std :utf8);

while (<STDIN>) {
  chomp;
  my ($id, $content) = split /,/, $_, 2;
  if (!defined $content) {
    print "$id,\n";
    next;
  }

  $content =~ s@[a-zA-Z]{3,7}://[-_○A-Za-z0-9./#%=?&]+@ @gu; # Delete things that looks remotely like URLs

  $content =~ s@(\\n|\\r|\\t|\\x[0-9a-f]+)@ @gu; # Delete apparent escape sequences

  $content =~ s/([^-\/+\$%@\p{L}\p{N}\p{Z}\p{S}]|[●])/ /gu; # Only keep things useful to us

  # Separate CJK things and non-CJK things
  my $charBlock = '[\p{CJK}\p{Bopomofo}\p{Hiragana}\p{Katakana}]';
  my $charBlockInv = '[^\p{CJK}\p{Bopomofo}\p{Hiragana}\p{Katakana}]';
  $content =~ s/($charBlock)($charBlockInv)/$1 $2/gu;
  $content =~ s/($charBlockInv)($charBlock)/$1 $2/gu;

  # Consolidate multiple spaces
  $content =~ s/\s+/ /gu;
  $content =~ s/^\s+//gu;
  $content =~ s/\s+$//gu;

  print "$id,$content\n";
}
