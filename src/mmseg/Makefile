CXX ?= g++
CXXFLAGS ?= -g0 -O3
LDFLAGS ?= -Wl,-O3

../../bin/mmseg: main.cc mmseg/mmseg.h mmseg/utf8cpp/utf8/checked.h mmseg/utf8cpp/utf8/core.h mmseg/utf8cpp/utf8/unchecked.h mmseg/utf8cpp/utf8.h
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -Immseg/ -std=c++23 -o $@ $^
