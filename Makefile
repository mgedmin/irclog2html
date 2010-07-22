PYTHON = python

.PHONY: default
default:
	@echo "Nothing to build here"

.PHONY: check
check:
	$(PYTHON) test_irclog2html.py
	$(PYTHON) test.py

