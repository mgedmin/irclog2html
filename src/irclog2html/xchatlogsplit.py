#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
Split xchat2 log file into daily log files suitable as input for logs2html.py.

Usage: xchatlogsplit.py filename

XXX code is ugly
"""

import sys
import time
import os
import re
import locale
from warnings import warn

STAMP_RX = re.compile(r'^[*][*][*][*] ((BEGIN|ENDING) LOGGING AT|(LOGINIMAS|ŽURNALAS) (PRADĖTAS|BAIGTAS)) ')

def readxchatlogs(infile):
    date = None
    ymd = None
    for line in infile:
        m = STAMP_RX.match(line)
        if m:
            stamp = line[len(m.group(0)):].strip()
            try:
                t = time.strptime(stamp, '%a %b %d %H:%M:%S %Y')
            except ValueError:
                locale.setlocale(locale.LC_TIME, "")
                t = time.strptime(stamp, '%a %b %d %H:%M:%S %Y')
                locale.setlocale(locale.LC_TIME, "C")

            ymd = t[:3]
            date = time.strftime("%Y-%m-%d", t)
        elif line.strip():
            assert date, 'what year?  got only %s' % line
            try:
                t = time.strptime(line[:len('Ddd YY HH:MM:SS'):], '%b %d %H:%M:%S')
            except ValueError:
                locale.setlocale(locale.LC_TIME, "")
                try:
                    t = time.strptime(stamp, '%a %b %d %H:%M:%S %Y')
                except:
                    warn("Skipping %s" % line.strip())
                    locale.setlocale(locale.LC_TIME, "C")
                    continue
                locale.setlocale(locale.LC_TIME, "C")
            t = (ymd[0], ) + t[1:]
            if t[:3] < ymd: # new year wraparound
                warn("Guessing that wraparound occurred: %s -> %s" % (ymd, t[:3]))
                t = (ymd[0] + 1, ) + t[1:]
            ymd = t[:3]
            date = time.strftime("%Y-%m-%d", t)
            line = line[len('Ddd YY '):]
        elif not date:
            continue

        assert date
        yield date, line

def main(argv=sys.argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    filename = argv[1]
    prefix = os.path.basename(filename).split('-')[1].split('.')[0]
    dir = os.path.dirname(filename)
    prefix = os.path.join(dir, prefix)
    curdate = None
    outfile = None
    for date, line in readxchatlogs(file(filename)):
        if curdate != date:
            if outfile: outfile.close()
            curdate = date
            outfilename = prefix + "." + date + ".log"
            if os.path.exists(outfilename):
                sys.exit("refusing to overwrite %s" % outfilename)
            outfile = open(outfilename, "a")
        print >> outfile, line,
    if outfile: outfile.close()

if __name__ == '__main__':
    main()
