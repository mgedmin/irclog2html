#!/usr/bin/env python
import doctest, irclog2html

if __name__ == '__main__':
    fail, total = doctest.testmod(irclog2html)
    if not fail:
        print "%d tests passed" % total
