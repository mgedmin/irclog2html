#!/usr/bin/env python
"""
Convert IRC logs to HTML.

Usage: irclog2html.py filename

irclog2html will write out a colourised irc log, appending a .html
extension to the output file.

This is a Python port of irclog2html.py Version 2.1, which
was written by Jeff Waugh and is available at www.perkypants.org
"""

# Copyright (c) 2005, Marius Gedminas 
# Copyright (c) 2000, Jeffrey W. Waugh

# Python port:
#   Marius Gedminas <marius@pov.lt>
# Original Author:
#   Jeff Waugh <jdub@perkypants.org>
# Contributors:
#   Rick Welykochy <rick@praxis.com.au>
#   Alexander Else <aelse@uu.net>
#
# Released under the terms of the GNU GPL
# http://www.gnu.org/copyleft/gpl.html

# Differences from the Perl version:
#   There are no hardcoded nick colour preferences for jdub, cantanker and
#   chuckd

import os
import re
import sys
import optparse

VERSION = "2.1"
RELEASE = "2005-01-09"

# $Id$

# Default colours for actions
DEFAULT_COLOURS = {
    "part":         "#000099",
    "join":         "#009900",
    "server":       "#009900",
    "nickchange":   "#009900",
    "action":       "#CC00CC",
}

# Hardcoded list of styles
STYLES = [
    ("simplett",     "Text style with little use of colour"),
    ("tt",           "Text style using colours for each nick"),
    ("simpletable",  "Table style, without heavy use of colour"),
    ("table",        "Default style, using a table with bold colours"),
]

# Precompiled regexps
URL_REGEXP = re.compile(r'(http|https|ftp|gopher|news)://\S*')
TIME_REGEXP = re.compile(r'^\[?(\d\d:\d\d(:\d\d)?)\]? ')
NICK_REGEXP = re.compile(r'^&lt;(.*?)&gt;\s')
NICK_CHANGE_REGEXP = re.compile(r'^(?:\*\*\*|---) (.*?)'
                                r' (?:are|is) now known as (.*)')

# Colouring stuff
a = 0.95        # tune these for the starting and ending concentrations of RGB
b = 0.5
RGB = [(a,b,b), (b,a,b), (b,b,a), (a,a,b), (a,b,a), (b,a,a)]
del a, b
RGBMIN = 240    # tune these two for the outmost ranges of colour depth
RGBMAX = 125

def html_rgb(i, ncolours):
    if ncolours == 0:
        ncolours = 1
    r, g, b = RGB[i % len(RGB)]
    m = RGBMIN + (RGBMAX - RGBMIN) * (ncolours - i) / ncolours
    r *= m
    g *= m
    r *= m
    return '#%02x%02x%02x' % (r, g, b)


def main():
    progname = os.path.basename(sys.argv[0])
    parser = optparse.OptionParser("usage: %prog [options] filename",
                                   description="Colourises and converts IRC"
                                               " logs to HTML format for easy"
                                               " web reading.")
    parser.add_option('-s', '--style', dest="style", default="table",
                      help="format log according to specific style"
                           " (default: table); try -s help for a list of"
                           " available styles")
    for item, value in DEFAULT_COLOURS.items():
        parser.add_option('--color-%s' % item, '--colour-%s' % item,
                          dest="colour_%s" % item, default=value,
                          help="select %s colour (default: %s)" % (item, value))
    options, args = parser.parse_args()
    if options.style == "help":
        print "The following styles are available for use with irclog2html.py:"
        for name, description in STYLES:
            print
            print "  %s" % name
            print "    %s" % description
        print
        return
    style = options.style
    if style not in [name for name, description in STYLES]:
        parser.error("unknown style: %s" % style)
    colours = {}
    for key in DEFAULT_COLOURS:
        colours[key] = getattr(options, 'colour_%s' % key)
    if not args:
        parser.error("required parameter missing")

    for filename in args:
        try:
            infile = open(filename)
        except EnvironmentError, e:
            sys.exit("%s: cannot open %s for reading: %s"
                     % (progname, filename, e))
        outfilename = filename + ".html"
        try:
            outfile = open(outfilename, "w")
        except EnvironmentError, e:
            infile.close()
            sys.exit("%s: cannot open %s for writing: %s"
                     % (progname, outfilename, e))
        try:
            log2html(infile, outfile, filename, style, colours)
        finally:
            outfile.close()
            infile.close()


def log2html(infile, outfile, title, style, colours, charset="iso-8859-1"):
    """Convert IRC log to HTML.

    `infile` and `outfile` are file objects.
    `colours` has the following attributes:
       part
       join
       server
       nickchange
       action
    """
    colour_nick = {}
    nickcount = 0
    nickmax = 30

    print >> outfile, """\
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
<html>
<head>
\t<title>%(title)s</title>
\t<meta name="generator" content="irclog2html.py %(VERSION)s by Marius Gedminas">
\t<meta name="version" content="%(VERSION)s - %(RELEASE)s">
\t<meta http-equiv="Content-Type" content="text/html; charset=%(charset)s">
</head>
<body text="#000000" bgcolor="#ffffff"><tt>
""" % {
        'VERSION': VERSION,
        'RELEASE': RELEASE,
        'title': title,
        'charset': charset,
    }

    if 'table' in style:
        print >> outfile, "<table cellspacing=3 cellpadding=2 border=0>"
    for line in infile:
        line = line.rstrip('\r\n')
        if not line:
            continue

        # Replace ampersands, pointies, control characters
        line = (line.replace('&', '&amp;')
                    .replace('<', '&lt;')
                    .replace('>', '&gt;'))
        line = ''.join([c for c in line if ord(c) > 0x1F])

        # Replace possible URLs with links
        line = URL_REGEXP.sub(r'<a href="\0">\0</a>', line)

        # Rip out the time
        time = TIME_REGEXP.match(line)
        if time:
            line = line[len(time.group(0)):]
            time = time.group(1)
            outfile.write(time)

        # Colourise the comments
        nick = NICK_REGEXP.match(line)
        if nick:
            # Split nick and line
            nick = nick.group(1)
            text = line[len(nick.group(0)):].replace('  ', '&nbsp;&nbsp;')

            htmlcolour = colour_nick.get(nick)
            if not htmlcolour:
                # new nick
                nickcount += 1
                # if we've exceeded our estimate of the number of nicks, double
                # it
                if nickcount >= nickmax:
                    nickmax *= 2
                htmlcolour = colour_nick[nick] = html_rgb(nickcount, nickmax)
            output_nicktext(outfile, style, nick, text, htmlcolour)
        else:
            # Colourise the /me's
            if line.startswith('* '):
                line = '<font color="%s">%s</font>' % (colours['action'], line)
            # Colourise joined/left messages #
            elif line.endswith('joined') and (line.startswith('*** ') or
                                              line.startswith('--&gt; ')):
                line = '<font color="%s">%s</font>' % (colours['join'], line)
            elif ((line.endswith('left') or line.endswith('quit')) and
                  (line.startswith('*** ') or line.startswith('--&gt; '))):
                line = '<font color="%s">%s</font>' % (colours['part'], line)
            # Process changed nick results, and remember colours accordingly
            elif ((line.startswith('*** ') or line.startswith('--- ')) and
                  (' are now known as ' in line or
                   ' is now known as ' in line)):
                m = NICK_CHANGE_REGEXP.match(line)
                assert m
                nick_old = m.group(1)
                nick_new = m.group(2)
                if nick_old in colour_nick:
                    colour_nick[nick_new] = colour_nick[nick_old]
                    del colour_nick[nick_old]
                line = '<font color="%s">%s</font>' % (colours['nickchange'],
                                                       line)
            # Server messages
            elif line.startswith('*** ') or line.startswith('--- '):
                line = '<font color="%s">%s</font>' % (colours['server'], line)

            output_servermsg(outfile, style, line)

    if 'table' in style:
        print >> outfile, "</table>"
    print >> outfile, """
<br>Generated by irclog2html.py %(VERSION)s by <a href="mailto:marius@pov.lt">Marius Gedminas</a>
 - find it at <a href="http://mg.pov.lt/irclog2html.py/">mg.pov.lt</a>!
</tt></body></html>""" % {'VERSION': VERSION, 'RELEASE': RELEASE}


def output_nicktext(outfile, style, nick, text, htmlcolour):
    if style == "table":
        print >> outfile, ('<tr><th bgcolor="%s"><font color="#ffffff">'
                           '<tt>%s</tt></font></th>'
                           '<td width="100%%" bgcolor="#eeeeee"><tt><font'
                           ' color="%s">%s<\/font></tt></td></tr>'
                           % (htmlcolour, nick, htmlcolour, text))
    elif style == "simpletable":
        print >> outfile, ('<tr><th bgcolor="#eeeeee"><font color="%s">'
                           '<tt>%s</tt></font></th>'
                           '<td width="100%%"><tt>%s</tt></td></tr>'
                           % (htmlcolour, nick, text))
    elif style == "simplett":
        print >> outfile, '&lt;%s&gt; %s<br>' % (nick, text)
    else:
        print >> outfile, ('<font color="%s">&lt;%s&gt;</font>'
                           ' <font color="#000000">%s</font><br>'
                           % (htmlcolour, nick, text))


def output_servermsg(outfile, style, line):
    if 'table' in style:
        print >> outfile, ('<tr><td colspan=2><tt>%s</tt></td></tr>'
                           % line)
    else:
        print >> outfile, '%s<br>' % line


if __name__ == '__main__':
    main()
