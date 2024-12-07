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

# Count the number of space-separated tokens in the "text" part of records

use strict;
use warnings;
use utf8;
use open qw(:std :utf8);

while (<STDIN>) {
  chomp;
  my ($key, $value) = split(/,/, $_, 2);
  if (!defined $value) {
    print "$key,0\n";
    next;
  }
  $value =~ s/^\s*//;
  $value =~ s/\s*$//;
  my @aToken = split(/\s+/, $value);

  my $len = @aToken;
  print "$key,$len\n";
}
