
SUBDIRS = $(wildcard */.)
LINKS = #$(foreach i,kenlm mitlm,../bin/$(i))

all: $(SUBDIRS) $(LINKS)

$(SUBDIRS):
	$(MAKE) -C $@

.PHONY: all $(SUBDIRS)
