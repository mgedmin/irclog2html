#!/usr/bin/env python
"""
Split xchat2 log file into daily log files suitable as input for logs2html.py.

Usage: xchatlogsplit.py filename

XXX code is ugly
"""

import sys
import time
import os
from warnings import warn


def readxchatlogs(infile):
    date = None
    ymd = None
    for line in infile:
        if line.startswith('**** BEGIN LOGGING AT '):
            t = time.strptime(line[len('**** BEGIN LOGGING AT '):].strip(),
                              '%a %b %d %H:%M:%S %Y')
            ymd = t[:3]
            date = time.strftime("%Y-%m-%d", t)
        elif line.startswith('**** ENDING LOGGING AT '):
            t = time.strptime(line[len('**** ENDING LOGGING AT '):].strip(),
                              '%a %b %d %H:%M:%S %Y')
            ymd = t[:3]
            date = time.strftime("%Y-%m-%d", t)
        elif line.strip():
            assert date
            try:
                t = time.strptime(line[:len('Ddd YY HH:MM:SS'):], '%b %d %H:%M:%S')
            except ValueError:
                warn("Skipping %s" % line.strip())
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
