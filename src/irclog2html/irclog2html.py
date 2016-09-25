#!/usr/bin/env python
"""
Convert IRC logs to HTML.

Usage: irclog2html.py filename

irclog2html will write out a colourised irc log, appending a .html
extension to the output file.

This is a Python port (+ improvements) of irclog2html.pl Version 2.1, which
was written by Jeff Waugh and is available at www.perkypants.org
"""

# Copyright (c) 2005--2014, Marius Gedminas
# Copyright (c) 2000, Jeffrey W. Waugh

# Python port:
#   Marius Gedminas <marius@pov.lt>
# Original Author:
#   Jeff Waugh <jdub@perkypants.org>
# Contributors:
#   Rick Welykochy <rick@praxis.com.au>
#   Alexander Else <aelse@uu.net>
#   Ian Weller <ianweller@gmail.com>
#
# Released under the terms of the GNU GPL
# http://www.gnu.org/copyleft/gpl.html

# Differences from the Perl version:
#   There are no hardcoded nick colour preferences for jdub, cantanker and
#   chuckd
#
#   Colours are preserver accross nick changes (irclog2html.pl tries to do
#   that, but its regexes are buggy)
#
#   irclog2html.pl interprets --colour-server #rrggbb as -s #rrggbb,
#   irclog2html.py does not have this bug
#
#   irclog2html.py understands ISO 8601 timestamps (YYYY-MM-DDTHH:MM:SS)
#
#   New options: --title, --{prev,index,next}-{url,title} and many more
#
#   New styles: xhtml, xhtmltable, mediawiki
#
#   New default style: xhtmltable
#

from __future__ import print_function, unicode_literals

import gzip
import io
import itertools
import optparse
import os
import re
import shlex
import shutil
import sys

try:
    from urllib import quote
except ImportError:
    from urllib.parse import quote

from ._version import __version__ as VERSION, __date__ as RELEASE

try:
    unicode
except NameError:
    # Python 3.x
    unicode = str


# If someone packages this for a Linux distro, they'll want to patch this to
# something like /usr/share/irclog2html/irclog.css, I imagine
CSS_FILE = os.path.join(os.path.dirname(__file__), 'irclog.css')


#
# Log parsing
#

class Enum(object):
    """Enumerated value."""

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return self.value


class LogParser(object):
    """Parse an IRC log file.

    When iterated, yields the following events:

        time, COMMENT, (nick, text)
        time, ACTION, text
        time, JOIN, text
        time, PART, text,
        time, NICKCHANGE, (text, oldnick, newnick)
        time, SERVER, text

    Text is a pure ASCII or Unicode string.
    """

    COMMENT = Enum('COMMENT')
    ACTION = Enum('ACTION')
    JOIN = Enum('JOIN')
    PART = Enum('PART')
    NICKCHANGE = Enum('NICKCHANGE')
    SERVER = Enum('SERVER')
    OTHER = Enum('OTHER')

    TIME_REGEXP = re.compile(
        r'^\[?(' # Optional [
        r'(?:\d{4}-\d{2}-\d{2}T|\d{2}-\w{3}-\d{4} |\w{3} \d{2} |\d{2} \w{3} )?' # Optional date
        r'\d\d:\d\d(:\d\d)?' # Mandatory HH:MM, optional :SS
        r')\]? +') # Optional ], mandatory space
    NICK_REGEXP = re.compile(r'^<(.*?)(!.*)?>\s')
    DIRCPROXY_NICK_REGEXP = re.compile(r'^<(.*?)(!.*)?>\s[\+-]?')
    JOIN_REGEXP = re.compile(r'^(?:\*\*\*|-->)\s.*joined')
    PART_REGEXP = re.compile(r'^(?:\*\*\*|<--)\s.*(quit|left)')
    SERVMSG_REGEXP = re.compile(r'^(?:\*\*\*|---)\s')
    NICK_CHANGE_REGEXP = re.compile(
        r'^(?:\*\*\*|---)\s+(.*?) (?:are|is) now known as (.*)')

    def __init__(self, infile, dircproxy=False):
        self.infile = infile
        if dircproxy:
            self.NICK_REGEXP = self.DIRCPROXY_NICK_REGEXP

    @staticmethod
    def decode(s):
        """Convert 8-bit string to Unicode.

        Supports xchat's hybrid Latin/Unicode encoding, as documented here:
        http://xchat.org/encoding/
        """
        if isinstance(s, unicode):
            # Accept input that's already Unicode, for convenience
            return s
        try:
            return s.decode('UTF-8')
        except UnicodeError:
            return s.decode('cp1252', 'replace')

    def __iter__(self):
        for line in self.infile:
            line = self.decode(line).rstrip('\r\n')
            if not line:
                continue

            m = self.TIME_REGEXP.match(line)
            if m:
                time = m.group(1)
                line = line[len(m.group(0)):]
            else:
                time = None

            m = self.NICK_REGEXP.match(line)
            if m:
                nick = m.group(1)
                text = line[len(m.group(0)):]
                yield time, self.COMMENT, (nick, text)
            elif line.startswith('* ') or line.startswith('*\t'):
                yield time, self.ACTION, line
            elif self.JOIN_REGEXP.match(line):
                yield time, self.JOIN, line
            elif self.PART_REGEXP.match(line):
                yield time, self.PART, line
            else:
                m = self.NICK_CHANGE_REGEXP.match(line)
                if m:
                    oldnick = m.group(1)
                    newnick = m.group(2)
                    line = line
                    yield time, self.NICKCHANGE, (line, oldnick, newnick)
                elif self.SERVMSG_REGEXP.match(line):
                    yield time, self.SERVER, line
                else:
                    yield time, self.OTHER, line


def open_log_file(filename):
    """Open a log file for parsing."""
    # We're dealing with text here.  Why open the file in binary mode?
    # Simple: the Latin/Unicode hybrid encoding monstrosity described
    # at http://xchat.org/encoding/#hybrid.  Python doesn't support this
    # natively, so we have to do the decoding ourselves.
    if filename.endswith('.gz'):
        return gzip.open(filename, 'rb')
    else:
        return io.open(filename, 'rb')


def shorttime(time):
    """Strip date and seconds from time.

        >>> print(shorttime('12:45:17'))
        12:45
        >>> print(shorttime('12:45'))
        12:45
        >>> print(shorttime('2005-02-04T12:45'))
        12:45

    """
    if 'T' in time:
        time = time.split('T')[-1]
    if time.count(':') > 1:
        time = ':'.join(time.split(':')[:2])
    return time


#
# Colouring stuff
#

class ColourChooser:
    """Choose distinguishable colours."""

    def __init__(self, rgbmin=240, rgbmax=125, a=0.95, b=0.5):
        """Define a range of colours available for choosing.

        `rgbmin` and `rgbmax` define the outmost range of colour depth (note
        that it is allowed to have rgbmin > rgbmax).

        `rgb`, if specified, is a list of (r,g,b) values where each component
        is between 0 and 1.0.

        If `rgb` is not specified, then it is constructed as
           [(a,b,b), (b,a,b), (b,b,a), (a,a,b), (a,b,a), (b,a,a)]

        You can tune `a` and `b` for the starting and ending concentrations of
        RGB.
        """
        assert 0 <= rgbmin < 256
        assert 0 <= rgbmax < 256
        self.rgbmin = rgbmin
        self.rgbmax = rgbmax
        assert 0 <= a <= 1.0
        assert 0 <= b <= 1.0
        self.rgb = [
            (a, b, b),
            (b, a, b),
            (b, b, a),
            (a, a, b),
            (a, b, a),
            (b, a, a),
        ]

    def choose(self, i, n):
        """Choose a colour.

        `n` specifies how many different colours you want in total.
        `i` identifies a particular colour in a set of `n` distinguishable
        colours.

        Returns a string '#rrggbb'.
        """
        if n == 0:
            n = 1
        r, g, b = self.rgb[i % len(self.rgb)]
        m = self.rgbmin + (self.rgbmax - self.rgbmin) * float(n - i) / n
        r, g, b = [int(c * m) for c in [r, g, b]]
        assert 0 <= r < 256
        assert 0 <= g < 256
        assert 0 <= b < 256
        return '#%02x%02x%02x' % (r, g, b)


class NickColourizer:
    """Choose distinguishable colours for nicknames."""

    def __init__(self, maxnicks=30, colour_chooser=None):
        """Create a colour chooser for nicknames.

        If you know how many different nicks there might be, specify that
        numer as `maxnicks`.  If you don't know, don't worry.

        If you really want to, you can specify a colour chooser.  Default is
        ColourChooser().
        """
        if colour_chooser is None:
            colour_chooser = ColourChooser()
        self.colour_chooser = colour_chooser
        self.nickcount = 0
        self.maxnicks = maxnicks
        self.nick_colour = {}

    def __getitem__(self, nick):
        colour = self.nick_colour.get(nick)
        if not colour:
            self.nickcount += 1
            if self.nickcount >= self.maxnicks:
                self.maxnicks *= 2
            colour = self.colour_chooser.choose(self.nickcount, self.maxnicks)
            self.nick_colour[nick] = colour
        return colour

    def change(self, oldnick, newnick):
        if oldnick in self.nick_colour:
            self.nick_colour[newnick] = self.nick_colour.pop(oldnick)


#
# HTML
#

URL_REGEXP = re.compile(r'((http|https|ftp|gopher|news)://([.,]*([^ \'")>&.,]|&amp;))*)')


def createlinks(text):
    """Replace possible URLs with links.

        >>> print(createlinks('check out &lt;http://example.com/a?b=c&amp;c=d#e&gt;!'))
        check out &lt;<a href="http://example.com/a?b=c&amp;c=d#e" rel="nofollow">http://example.com/a?b=c&amp;c=d#e</a>&gt;!

        >>> print(createlinks('http://example.com/a,'))
        <a href="http://example.com/a" rel="nofollow">http://example.com/a</a>,

        >>> print(createlinks('http://example.com/a.'))
        <a href="http://example.com/a" rel="nofollow">http://example.com/a</a>.

        >>> print(createlinks('http://example.com/a.b'))
        <a href="http://example.com/a.b" rel="nofollow">http://example.com/a.b</a>

    """
    return URL_REGEXP.sub(r'<a href="\1" rel="nofollow">\1</a>', text)


def escape(s):
    """Replace ampersands, pointies, control characters.

        >>> print(escape('"Hello" & <world>'))
        &quot;Hello&quot; &amp; &lt;world&gt;

    Control characters (ASCII 0 to 31) are stripped away

        >>> print(escape('[%s]' % ''.join([chr(x) for x in range(32)])))
        []

    """
    s = s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
    return ''.join([c for c in s if ord(c) > 0x1F])


#
# Output styles
#

class AbstractStyle(object):
    """A style defines the way output is formatted.

    This is not a real class, rather it is an description of how style
    classes should be written.
    """

    name = "stylename"
    description = "Single-line description"
    charset = 'US-ASCII'

    def __init__(self, outfile, colours=None):
        """Create a text formatter for writing to outfile.

        The ``colours`` dictionary may have the following items:

        - part
        - join
        - server
        - nickchange
        - action

        """
        self.outfile = io.TextIOWrapper(outfile, encoding=self.charset,
                                        errors='xmlcharrefreplace',
                                        line_buffering=True)
        self.colours = colours or {}
        self._anchors = set()

    def __del__(self):
        """Destructor to make sure we don't close outfile prematurely."""
        if not self.outfile.closed:
            self.outfile.flush()
            self.outfile.detach()  # don't let TextIOWrapper.__del__ close it!

    def head(self, title, prev=('', ''), index=('', ''), next=('', ''),
             searchbox=False):
        """Generate the header.

        `prev`, `index` and `next` are tuples (title, url) that comprise
        the navigation bar.
        """

    def foot(self):
        """Generate the footer."""

    def servermsg(self, time, what, line):
        """Output a generic server message.

        `time` is a string.
        `line` is not escaped.
        `what` is one of LogParser event constants (e.g. LogParser.JOIN).
        """

    def nicktext(self, time, nick, text, htmlcolour):
        """Output a comment uttered by someone.

        `time` is a string.
        `nick` and `text` are not escaped.
        `htmlcolour` is a string ('#rrggbb').
        """

    def timestamp_anchor(self, time):
        anchor = 't%s' % time
        if anchor in self._anchors:
            for n in itertools.count(2):
                anchor = '%s-%d' % (anchor, n)
                if anchor not in self._anchors:
                    break
        self._anchors.add(anchor)
        return anchor


class SimpleTextStyle(AbstractStyle):
    """Text style with little use of colour"""

    name = "simplett"
    description = __doc__
    charset = 'iso-8859-1'

    def head(self, title, prev=None, index=None, next=None, searchbox=False):
        print("""\
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
<html>
<head>
\t<title>%(title)s</title>
\t<meta name="generator" content="irclog2html.py %(VERSION)s by Marius Gedminas">
\t<meta name="version" content="%(VERSION)s - %(RELEASE)s">
\t<meta http-equiv="Content-Type" content="text/html; charset=%(charset)s">
</head>
<body text="#000000" bgcolor="#ffffff"><tt>""" % {
            'VERSION': VERSION,
            'RELEASE': RELEASE,
            'title': escape(title),
            'charset': self.charset,
        }, file=self.outfile)

    def foot(self):
        print("""
<br>Generated by irclog2html.py %(VERSION)s by <a href="mailto:marius@pov.lt">Marius Gedminas</a>
 - find it at <a href="http://mg.pov.lt/irclog2html/">mg.pov.lt</a>!
</tt></body></html>""" % {'VERSION': VERSION, 'RELEASE': RELEASE}, end=' ', file=self.outfile)

    def servermsg(self, time, what, text):
        text = escape(text)
        text = createlinks(text)
        colour = self.colours.get(what)
        if colour:
            text = '<font color="%s">%s</font>' % (colour, text)
        self._servermsg(text)

    def _servermsg(self, line):
        print('%s<br>' % line, file=self.outfile)

    def nicktext(self, time, nick, text, htmlcolour):
        nick = escape(nick)
        text = escape(text)
        text = createlinks(text)
        text = text.replace('  ', '&nbsp;&nbsp;')
        self._nicktext(time, nick, text, htmlcolour)

    def _nicktext(self, time, nick, text, htmlcolour):
        print('&lt;%s&gt; %s<br>' % (nick, text), file=self.outfile)


class TextStyle(SimpleTextStyle):
    """Text style using colours for each nick"""

    name = "tt"
    description = __doc__

    def _nicktext(self, time, nick, text, htmlcolour):
        print('<font color="%s">&lt;%s&gt;</font>'
              ' <font color="#000000">%s</font><br>'
              % (htmlcolour, nick, text), file=self.outfile)


class SimpleTableStyle(SimpleTextStyle):
    """Table style, without heavy use of colour"""

    name = "simpletable"

    def head(self, title, prev=None, index=None, next=None, searchbox=False):
        SimpleTextStyle.head(self, title, prev, index, next, searchbox)
        print("<table cellspacing=3 cellpadding=2 border=0>", file=self.outfile)

    def foot(self):
        print("</table>", file=self.outfile)
        SimpleTextStyle.foot(self)

    def _servermsg(self, line):
        print('<tr><td colspan=2><tt>%s</tt></td></tr>' % line,
              file=self.outfile)

    def _nicktext(self, time, nick, text, htmlcolour):
        print('<tr bgcolor="#eeeeee"><th><font color="%s">'
              '<tt>%s</tt></font></th>'
              '<td width="100%%"><tt>%s</tt></td></tr>'
              % (htmlcolour, nick, text), file=self.outfile)


class TableStyle(SimpleTableStyle):
    """Default style, using a table with bold colours"""

    name = "table"
    description = __doc__

    def _nicktext(self, time, nick, text, htmlcolour):
        print('<tr><th bgcolor="%s"><font color="#ffffff">'
              '<tt>%s</tt></font></th>'
              '<td width="100%%" bgcolor="#eeeeee"><tt><font color="%s">%s</font></tt></td></tr>'
              % (htmlcolour, nick, htmlcolour, text), file=self.outfile)


class XHTMLStyle(AbstractStyle):
    """Text style, produces XHTML that can be styled with CSS"""

    name = 'xhtml'
    description = __doc__
    charset = 'UTF-8'

    CLASSMAP = {
        LogParser.ACTION: 'action',
        LogParser.JOIN: 'join',
        LogParser.PART: 'part',
        LogParser.NICKCHANGE: 'nickchange',
        LogParser.SERVER: 'servermsg',
        LogParser.OTHER: 'other',
    }

    prefix = '<div class="irclog">'
    suffix = '</div>'

    def head(self, title, prev=('', ''), index=('', ''), next=('', ''),
             searchbox=False):
        self.prev = prev
        self.index = index
        self.next = next
        print("""\
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
          "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html>
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=%(charset)s" />
  <title>%(title)s</title>
  <link rel="stylesheet" href="irclog.css" />
  <meta name="generator" content="irclog2html.py %(VERSION)s by Marius Gedminas" />
  <meta name="version" content="%(VERSION)s - %(RELEASE)s" />
</head>
<body>""" % {'VERSION': VERSION, 'RELEASE': RELEASE,
             'title': escape(title), 'charset': self.charset}, file=self.outfile)
        self.heading(title)
        if searchbox:
            self.searchbox()
        self.navbar(prev, index, next)
        print(self.prefix, file=self.outfile)

    def heading(self, title):
        print('<h1>%s</h1>' % escape(title), file=self.outfile)

    def link(self, url, title):
        # Intentionally not escaping title so that &entities; work
        if url:
            print('<a href="%s">%s</a>'
                  % (escape(quote(url)), title or escape(url)),
                  end=' ', file=self.outfile)
        elif title:
            print('<span class="disabled">%s</span>' % title,
                  end=' ', file=self.outfile)

    def searchbox(self):
        print("""
<div class="searchbox">
<form action="search" method="get">
<input type="text" name="q" id="searchtext" />
<input type="submit" value="Search" id="searchbutton" />
</form>
</div>
""", file=self.outfile)

    def navbar(self, prev, index, next):
        prev_title, prev_url = prev
        index_title, index_url = index
        next_title, next_url = next
        if not (prev_title or index_title or next_title or
                prev_url or index_url or next_url):
            return
        print('<div class="navigation">', end=' ', file=self.outfile)
        self.link(prev_url, prev_title)
        self.link(index_url, index_title)
        self.link(next_url, next_title)
        print('</div>', file=self.outfile)

    def foot(self):
        print(self.suffix, file=self.outfile)
        self.navbar(self.prev, self.index, self.next)
        print("""
<div class="generatedby">
<p>Generated by irclog2html.py %(VERSION)s by <a href="mailto:marius@pov.lt">Marius Gedminas</a>
 - find it at <a href="http://mg.pov.lt/irclog2html/">mg.pov.lt</a>!</p>
</div>
</body>
</html>""" % {'VERSION': VERSION, 'RELEASE': RELEASE}, file=self.outfile)

    def servermsg(self, time, what, text):
        """Output a generic server message.

        `time` is a string.
        `line` is not escaped.
        `what` is one of LogParser event constants (e.g. LogParser.JOIN).
        """
        text = escape(text)
        text = createlinks(text)
        if time:
            print(
                '<p id="{anchor}" class="{css_class}">'
                '<a href="#{anchor}" class="time">{time}</a>'
                ' {text}</p>'.format(
                    anchor=self.timestamp_anchor(time),
                    css_class=self.CLASSMAP[what],
                    time=shorttime(time),
                    text=text),
                file=self.outfile)
        else:
            print(
                '<p class="{css_class}">{text}</p>'.format(
                    css_class=self.CLASSMAP[what], text=text),
                file=self.outfile)

    def nicktext(self, time, nick, text, htmlcolour):
        """Output a comment uttered by someone.

        `time` is a string.
        `nick` and `text` are not escaped.
        `htmlcolour` is a string ('#rrggbb').
        """
        nick = escape(nick)
        text = escape(text)
        text = createlinks(text)
        text = text.replace('  ', '&nbsp;&nbsp;')
        if time:
            print(
                '<p id="{anchor}" class="comment">'
                '<a href="#{anchor}" class="time">{time}</a> '
                '<span class="nick" style="color: {color}">'
                '&lt;{nick}&gt;</span>'
                ' <span class="text">{text}</span></p>'.format(
                    anchor=self.timestamp_anchor(time),
                    time=shorttime(time),
                    color=htmlcolour,
                    nick=nick,
                    text=text),
                file=self.outfile)
        else:
            print(
                '<p class="comment">'
                '<span class="nick" style="color: {color}">'
                '&lt;{nick}&gt;</span>'
                ' <span class="text">{text}</span></p>'.format(
                    color=htmlcolour,
                    nick=nick,
                    text=text),
                file=self.outfile)


class XHTMLTableStyle(XHTMLStyle):
    """Table style, produces XHTML that can be styled with CSS"""

    name = 'xhtmltable'
    description = __doc__

    prefix = '<table class="irclog">'
    suffix = '</table>'

    def servermsg(self, time, what, text, link=''):
        text = escape(text)
        text = createlinks(text)
        if time:
            print(
                '<tr id="{anchor}">'
                '<td class="{css_class}" colspan="2">{text}</td>'
                '<td><a href="{link}#{anchor}" class="time">{time}</a></td>'
                '</tr>'.format(
                    anchor=self.timestamp_anchor(time),
                    css_class=self.CLASSMAP[what],
                    text=text,
                    link=link,
                    time=shorttime(time)),
                file=self.outfile)
        else:
            print(
                '<tr>'
                '<td class="{css_class}" colspan="3">{text}</td>'
                '</tr>'.format(
                    css_class=self.CLASSMAP[what],
                    text=text),
                file=self.outfile)

    def nicktext(self, time, nick, text, htmlcolour, link=''):
        nick = escape(nick)
        text = escape(text)
        text = createlinks(text)
        text = text.replace('  ', '&nbsp;&nbsp;')
        if time:
            print(
                '<tr id="{anchor}">'
                '<th class="nick" style="background: {color}">{nick}</th>'
                '<td class="text" style="color: {color}">{text}</td>'
                '<td class="time">'
                '<a href="{link}#{anchor}" class="time">{time}</a></td>'
                '</tr>'.format(
                    anchor=self.timestamp_anchor(time),
                    color=htmlcolour,
                    nick=nick,
                    text=text,
                    link=link,
                    time=shorttime(time)),
                file=self.outfile)
        else:
            print(
                '<tr>'
                '<th class="nick" style="background: {color}">{nick}</th>'
                '<td class="text" colspan="2" style="color: {color}">{text}</td>'
                '</tr>'.format(
                    color=htmlcolour,
                    nick=nick,
                    text=text),
                file=self.outfile)


class MediaWikiStyle(AbstractStyle):
    """Table style, produces MediaWiki syntax"""

    name = 'mediawiki'
    description = __doc__

    def head(self, title, prev=('', ''), index=('', ''), next=('', ''),
             searchbox=False):
        print('{|', file=self.outfile)

    def servermsg(self, time, what, text, link=''):
        text = escape(text)
        # no need to call createlinks, MediaWiki parses links automatically
        if time:
            displaytime = shorttime(time)
            print('|- id="t%s"\n'
                  '| colspan="2" | %s\n'
                  '|| [[#t%s|%s]]'
                  % (time, text, time, displaytime), file=self.outfile)
        else:
            print('|-\n'
                  '| colspan="3" | %s' % text, file=self.outfile)

    def nicktext(self, time, nick, text, htmlcolour, link=''):
        nick = escape(nick)
        text = escape(text)
        # no need to call createlinks, MediaWiki parses links automatically
        if time:
            displaytime = shorttime(time)
            print('|- id="t%s"\n'
                  '! style="background-color: %s" | %s\n'
                  '| style="color: %s" | %s\n'
                  '|| [[#t%s|%s]] '
                  % (time, htmlcolour, nick, htmlcolour, text,
                     time, displaytime), file=self.outfile)
        else:
            print('|-\n'
                  '| style="background-color: %s" | %s\n'
                  '| style="color: %s" colspan="2" | %s '
                  % (htmlcolour, nick, htmlcolour, text), file=self.outfile)

    def foot(self):
        print('|}\n\nGenerated by irclog2html.py %(VERSION)s '
              'by [mailto:marius@pov.lt Marius Gedminas] - '
              'find it at [http://mg.pov.lt/irclog2html '
              'mg.pov.lt]!'
              % {'VERSION': VERSION}, file=self.outfile)


#
# Main
#

# All styles
STYLES = [
    SimpleTextStyle,
    TextStyle,
    SimpleTableStyle,
    TableStyle,
    XHTMLStyle,
    XHTMLTableStyle,
    MediaWikiStyle,
]

# Customizable colours
COLOURS = [
    ("part",       "#000099", LogParser.PART),
    ("join",       "#009900", LogParser.JOIN),
    ("server",     "#009900", LogParser.SERVER),
    ("nickchange", "#009900", LogParser.NICKCHANGE),
    ("action",     "#CC00CC", LogParser.ACTION),
]


def do_config_file(option, opt_str, value, parser):
    """Read options from a config file and feed them back to optparse."""
    options = []
    try:
        with open(value) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                options.extend(shlex.split(line))
        # Note: you can cause an infinite loop if you have a config file that
        # includes itself!  Well, cause a RuntimeError actually.
        parser.rargs[:0] = options
    except IOError as e:
        raise optparse.OptionValueError("can't read config file: %s" % e)


def parse_args(argv=sys.argv):
    progname = os.path.basename(argv[0])
    parser = optparse.OptionParser("usage: %prog [options] filename [...]",
                                   prog=progname,
                                   version=VERSION,
                                   description="Colourises and converts IRC"
                                               " logs to HTML format for easy"
                                               " web reading.")
    parser.add_option('-c', '--config', action='callback', type='str',
                      metavar='FILE', callback=do_config_file,
                      help="read options from a config file")
    parser.add_option('--dircproxy', action='store_true', default=False,
                      help="dircproxy log file support (strips leading + or - from messages; off by default)")
    parser.add_option('-s', '--style', dest="style", default="xhtmltable",
                      help="format log according to specific style"
                           " (default: xhtmltable); try -s help for a list of"
                           " available styles")
    parser.add_option('-t', '--title', dest="title", default=None,
                      help="title of the page (default: same as file name)")
    parser.add_option('--prev-title', dest="prev_title", default='',
                      help="title of the previous page (default: none)")
    parser.add_option('--prev-url', dest="prev_url", default='',
                      help="URL of the previous page (default: none)")
    parser.add_option('--index-title', dest="index_title", default='',
                      help="title of the index page (default: none)")
    parser.add_option('--index-url', dest="index_url", default='',
                      help="URL of the index page (default: none)")
    parser.add_option('--next-title', dest="next_title", default='',
                      help="title of the next page (default: none)")
    parser.add_option('--next-url', dest="next_url", default='',
                      help="URL of the next page (default: none)")
    parser.add_option('-S', '--searchbox', action="store_true", dest="searchbox",
                      default=False,
                      help="include a search box")
    parser.add_option('-o', '--output-file',
                      help="destination output file or directory"
                           " (default: <input-file-name>.html)")
    for name, default, what in COLOURS:
        parser.add_option('--color-%s' % name, '--colour-%s' % name,
                          dest="colour_%s" % name, default=default,
                          help="select %s colour (default: %s)"
                               % (name, default))
    options, args = parser.parse_args(argv[1:])
    return parser, options, args


def pick_output_filename(input_filename):
    """Pick a filename for the output file."""
    if input_filename.endswith('.gz'):
        return input_filename[:-len('.gz')] + ".html"
    else:
        return input_filename + ".html"


def main(argv=sys.argv):
    parser, options, args = parse_args(argv)
    if options.style == "help":
        print("The following styles are available for use with irclog2html.py:")
        for style in STYLES:
            print()
            print("  %s" % style.name)
            print("    %s" % style.description)
        print()
        return
    for style in STYLES:
        if style.name == options.style:
            break
    else:
        parser.error("unknown style: %s" % options.style)
    colours = {}
    for name, default, what in COLOURS:
        colours[what] = getattr(options, 'colour_%s' % name)
    if not args:
        parser.error("please specify a filename")
    title = options.title
    prev = (options.prev_title, options.prev_url)
    index = (options.index_title, options.index_url)
    next = (options.next_title, options.next_url)

    if len(args) > 1 and options.output_file and not os.path.isdir(options.output_file):
        parser.error("-o must be a directory when processing multiple files")
    for filename in args:
        try:
            infile = open_log_file(filename)
        except EnvironmentError as e:
            sys.exit("%s: cannot open %s for reading: %s"
                     % (parser.prog, filename, e))
        # Why open the output file in binary mode?  We currently handle
        # encoding in our style classes, and they have different default
        # charsets, so it's simpler to just give a binary file to the
        # style class and let it deal with all the details.
        if not options.output_file:
            outfilename = pick_output_filename(filename)
        elif os.path.isdir(options.output_file):
            outfilename = os.path.join(
                options.output_file,
                os.path.basename(pick_output_filename(filename)))
        else:
            outfilename = options.output_file
        try:
            outfile = io.open(outfilename, "wb")
        except EnvironmentError as e:
            infile.close()
            sys.exit("%s: cannot open %s for writing: %s"
                     % (parser.prog, outfilename, e))
        try:
            parser = LogParser(infile, dircproxy=options.dircproxy)
            formatter = style(outfile, colours)
            convert_irc_log(parser, formatter, title or filename,
                            prev, index, next, searchbox=options.searchbox)
            css_file = os.path.join(os.path.dirname(outfilename), 'irclog.css')
            if not os.path.exists(css_file) and os.path.exists(CSS_FILE):
                shutil.copy(CSS_FILE, css_file)
        finally:
            outfile.close()
            infile.close()


def convert_irc_log(parser, formatter, title, prev, index, next,
                    searchbox=False):
    """Convert IRC log to HTML or some other format."""
    nick_colour = NickColourizer()
    formatter.head(title, prev, index, next, searchbox=searchbox)
    for time, what, info in parser:
        if what == LogParser.COMMENT:
            nick, text = info
            htmlcolour = nick_colour[nick]
            formatter.nicktext(time, nick, text, htmlcolour)
        else:
            if what == LogParser.NICKCHANGE:
                text, oldnick, newnick = info
                nick_colour.change(oldnick, newnick)
            else:
                text = info
            formatter.servermsg(time, what, text)
    formatter.foot()


if __name__ == '__main__':
    main()
