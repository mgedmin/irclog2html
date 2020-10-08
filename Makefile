PYTHON = python
PAGER = less -RFX
TESTFLAGS = -v

FILE_WITH_VERSION = src/irclog2html/_version.py
FILE_WITH_CHANGELOG = CHANGES.rst

scripts = bin/test bin/irclog2html bin/logs2html bin/irclogsearch bin/irclogserver

SHELL = /bin/bash -o pipefail


.PHONY: default
default: all


.PHONY: all
all: $(scripts)


.PHONY: check test
check test:
	tox -p auto

.PHONY: flake8 lint
flake8 lint:
	tox -e flake8

.PHONY: test-all-pythons
test-all-pythons:
	tox

.PHONY: coverage
coverage:
	tox -e coverage2,coverage3

.PHONY: diff-cover
diff-cover: coverage
	tox -e coverage
	coverage xml
	diff-cover coverage.xml

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
