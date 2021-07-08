PYTHON = python3

scripts = bin/test bin/irclog2html bin/logs2html bin/irclogsearch bin/irclogserver


.PHONY: all
all: $(scripts)         ##: build a local buildout with all the scripts


.PHONY: test
test:                   ##: run tests
	tox -p auto

.PHONY: flake8
flake8:                 ##: check for style problems
	tox -e flake8

.PHONY: coverage
coverage:               ##: measure test coverage
	tox -e coverage2,coverage3

.PHONY: diff-cover
diff-cover:             ##: find untested code on this branch
	tox -e coverage
	coverage xml
	diff-cover coverage.xml

.PHONY: clean
clean:                  ##: clean up build artifacts
	rm -f testcases/*.html testcases/*.css


.PHONY: releasechecklist
releasechecklist: check-date  # also release.mk will add other checks


FILE_WITH_VERSION = src/irclog2html/_version.py
FILE_WITH_METADATA = src/irclog2html/_version.py
include release.mk

# override the release recipe in release.mk
define release_recipe =
$(default_release_recipe_publish_and_tag)
$(default_release_recipe_increment_and_push)
	@echo "Then please go to https://github.com/mgedmin/irclog2html/tags"
	@echo "and convert the $(changelog_ver) tag into a release."
endef

.PHONY: check-date
check-date:
	@date_line="__date__ = '"`date +%Y-%m-%d`"'" && \
	    grep -q "^$$date_line$$" $(FILE_WITH_METADATA) || { \
	        echo "$(FILE_WITH_METADATA) doesn't specify $$date_line"; \
	        echo "Please run make update-date"; exit 1; }

.PHONY: update-date
update-date:                    ##: set release date in source code to today
	sed -i -e "s/^__date__ = '.*'/__date__ = '"`date +%Y-%m-%d`"'/" $(FILE_WITH_METADATA)


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
