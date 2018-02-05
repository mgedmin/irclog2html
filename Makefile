PYTHON = python
PAGER = less -RFX
TESTFLAGS = -v

FILE_WITH_VERSION = src/irclog2html/_version.py
FILE_WITH_CHANGELOG = CHANGES.rst

scripts = bin/test bin/irclog2html bin/logs2html bin/irclogsearch bin/irclogserver

SHELL = /bin/bash -o pipefail


ifneq "$(TERM)" "dumb"
is_tty = $(shell test -t 2 && echo 1)
endif


.PHONY: default
default: all


.PHONY: all
all: $(scripts)


.PHONY: check test
check test: bin/test
ifdef is_tty
	bin/test $(TESTFLAGS) -c | $(PAGER)
else
	bin/test $(TESTFLAGS)
endif

.PHONY: test-all-pythons
test-all-pythons:
	tox

.PHONY: coverage
coverage:
	tox -e coverage,coverage3 -- -p
	coverage combine
	coverage report -m --fail-under=100

.PHONY: clean
clean:
	rm -f testcases/*.html testcases/*.css


.PHONY: releasechecklist
releasechecklist: check-date  # also release.mk will add other checks

include release.mk

.PHONY: check-date
check-date:
	@date_line="__date__ = '`date +%Y-%m-%d`'" && \
	    grep -q "^$$date_line$$" $(FILE_WITH_VERSION) || { \
	        echo "$(FILE_WITH_VERSION) doesn't specify $$date_line"; exit 1; }


python:
	virtualenv -p $(PYTHON) python

python/bin/virtualenv:
	python/bin/pip install -U setuptools virtualenv

bin/buildout: python bootstrap.py
	python/bin/pip install -U setuptools
	python/bin/python bootstrap.py
	touch -c $@


$(scripts): bin/buildout buildout.cfg setup.py python/bin/virtualenv
	bin/buildout
	touch -c $(scripts)
