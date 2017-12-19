PYTHON = python
PAGER = less -RFX
TESTFLAGS = -v

FILE_WITH_VERSION = src/irclog2html/_version.py
FILE_WITH_CHANGELOG = CHANGES.rst

scripts = bin/test bin/irclog2html bin/logs2html bin/irclogsearch bin/irclogserver bin/tox

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
test-all-pythons: bin/tox
	bin/tox

.PHONY: coverage
coverage: bin/tox
	bin/tox -e coverage,coverage3 -- -p
	bin/coverage combine
	bin/coverage report

.PHONY: clean
clean:
	rm -f testcases/*.html testcases/*.css


include release.mk


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
