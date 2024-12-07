// Copyright 2020-2024, Hojin Koh
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// A simple command-line program to read lines from stdin and do segmentation
// Using modified mmseg library https://github.com/jdeng/mmseg
// which is MIT-licensed

#include <algorithm> // for find_if_not
#include <iostream> // for reading stdin
#include <spanstream> // for comma delimiter part
#include <string>
#include <string_view>

#include "mmseg.h"

bool isSpace(char c) {
  return std::isspace(static_cast<unsigned char>(c));
}

std::string_view strip(std::string_view str) {
  auto start = std::find_if_not(str.begin(), str.end(), isSpace);
  auto end = std::find_if_not(str.rbegin(), str.rend(), isSpace).base(); // reverse search for end
  return start == end ? "" : std::string_view(start, end); 
}

int main(int argc, char* argv[]) {
  if (argc < 3) {
    std::cerr << "Usage: " << argv[0] << " <word-dict> <char-dict>\n";
    return 1;
  }

  MMSeg mmseg;
  mmseg.load(argv[1], argv[2]);

  for (std::string line; std::getline(std::cin, line);) {
    std::ispanstream iss(strip(line));
    std::string eid, text;

    std::getline(iss, eid, ','); // Read up to the comma delimiter
    std::getline(iss, text); // Read the rest of the line
    auto textStripped = strip(text);
    std::cout << eid << ',';
    if (textStripped.size() == 0) {
      std::cout << '\n';
      continue;
    }

    // Try to separate the different parts of the input text
    bool isFirstSeg = true;
    for (auto it = textStripped.begin(); it != textStripped.end();) {
      it = std::find_if_not(it, textStripped.end(), isSpace);

      // Find the next code-switching boundary or end of string
      auto end = std::find_if(it, textStripped.end(), [&](char c) {
          return (c & 0x80) != (*it & 0x80); // Different ASCII/non-ASCII
          });

      if (it == end) break;

      std::string_view strSeg = strip(std::string_view(it, end));
      if (isFirstSeg) {
        isFirstSeg = false;
      } else {
        std::cout << " ";
      }

      // ASCII Part: just print it out
      if (static_cast<unsigned char>(*it) < 0x80) {
        std::cout << strSeg;
      } else { // Non-ASCII Part: need segmentation
        std::u32string s;
        try {
          s = MMSeg::from_utf8(std::string(strSeg));
          bool isFirstWord = true;
          for (auto& w: mmseg.segment(s)) {
            if (isFirstWord) {
              isFirstWord = false;
            } else {
              std::cout << " ";
            }
            std::cout << MMSeg::to_utf8(w);
          }
        } catch(const std::exception& e) {
          std::cerr << "ERROR converting to/from UTF-32 (" << eid << "): " << strSeg << std::endl;
        }
      }

      it = end;
    } // End for text segments
    std::cout << '\n';
  } // End for each line
  return 0;
}
