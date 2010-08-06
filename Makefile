PYTHON = python
PAGER = less -RFX
TESTFLAGS = -vc


.PHONY: default
default: all


.PHONY: all
all: bin/buildout bin/test


.PHONY: check test
check test: bin/test
ifdef PAGER
	bin/test $(TESTFLAGS) | $(PAGER)
else
	bin/test $(TESTFLAGS)
endif


.PHONY: clean
clean:
	rm -f testcases/*.html


bin/buildout: bootstrap.py
	$(PYTHON) bootstrap.py


bin/test bin/irclog2html bin/logs2html bin/irclogsearch: bin/buildout buildout.cfg setup.py
	bin/buildout
	touch $@
