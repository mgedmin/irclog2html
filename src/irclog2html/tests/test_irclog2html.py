from __future__ import print_function

import doctest
import io
import os
import shutil
import sys
import tempfile
import unittest

from irclog2html.irclog2html import (
    LogParser, ColourChooser, NickColourizer,
    SimpleTextStyle, TextStyle, SimpleTableStyle, TableStyle,
    XHTMLStyle, XHTMLTableStyle, MediaWikiStyle,
    COLOURS, parse_args, main)


try:
    unicode
except NameError:
    # Python 3.x
    unicode = str


here = os.path.dirname(__file__)


def myrepr(o):
    """Repr that drops u prefixes on unicode strings."""
    if isinstance(o, tuple):
        if len(o) == 1:
            return '(%s, )' % ', '.join(map(myrepr, o))
        else:
            return '(%s)' % ', '.join(map(myrepr, o))
    elif isinstance(o, unicode):
        return repr(o).lstrip('u')
    else:
        return repr(o)


def doctest_LogParser():
    r"""Tests for LogParser

    I'll define a helper function to test parsing.

        >>> def test(line):
        ...     for time, what, info in LogParser([line]):
        ...         print(myrepr(time), what, myrepr(info))

    LogParser ignores empty lines

        >>> test('')
        >>> test('\n')
        >>> test('\r\n')

    All other lines result in a tuple (time, what, info)

        >>> test('14:18 * mg says Hello')
        '14:18' ACTION '* mg says Hello'

    Usually `info` is a string, but sometimes it is a tuple

        >>> test('14:18 <mg> Hello!')
        '14:18' COMMENT ('mg', 'Hello!')

    Newline characters are stripped from the line, if they are present

        >>> test('14:18 * mg says Hello\n')
        '14:18' ACTION '* mg says Hello'
        >>> test('14:18 * mg says Hello\r\n')
        '14:18' ACTION '* mg says Hello'
        >>> test('14:18 * mg says Hello\r')
        '14:18' ACTION '* mg says Hello'

    If there is no timestamp on the line, LogParser returns None

        >>> test('* mg says Hello')
        None ACTION '* mg says Hello'

    Several timestamp formats are recognized

        >>> test('14:18 <mg> Hello!')
        '14:18' COMMENT ('mg', 'Hello!')
        >>> test('[14:18] <mg> Hello!')
        '14:18' COMMENT ('mg', 'Hello!')
        >>> test('[14:18:55] <mg> Hello!')
        '14:18:55' COMMENT ('mg', 'Hello!')
        >>> test('[2004-02-04T14:18:55] <mg> Hello!')
        '2004-02-04T14:18:55' COMMENT ('mg', 'Hello!')
        >>> test('[02-Feb-2004 14:18:55] <mg> Hello!')
        '02-Feb-2004 14:18:55' COMMENT ('mg', 'Hello!')
        >>> test('[15 Jan 08:42] <mg> +++Hello+++')
        '15 Jan 08:42' COMMENT ('mg', '+++Hello+++')

    Excessive metainformation is stripped from nicknames

        >>> test('[15 Jan 08:42] <jsmith!n=jsmith@10.20.30.40> Hello!')
        '15 Jan 08:42' COMMENT ('jsmith', 'Hello!')

    `what` can be COMMENT...

        >>> test('<nick> text')
        None COMMENT ('nick', 'text')

    ...ACTION...

        >>> test('* nick text')
        None ACTION '* nick text'
        >>> test('*\tnick text')
        None ACTION '*\tnick text'

    ...JOIN...

        >>> test('*** someone joined #channel')
        None JOIN '*** someone joined #channel'
        >>> test('--> someone joined')
        None JOIN '--> someone joined'

    ...PART...

        >>> test('*** someone quit')
        None PART '*** someone quit'
        >>> test('<-- someone left #channel')
        None PART '<-- someone left #channel'

    ...NICKCHANGE...

        >>> test('*** X is now known as Y')
        None NICKCHANGE ('*** X is now known as Y', 'X', 'Y')
        >>> test('--- X are now known as Y')
        None NICKCHANGE ('--- X are now known as Y', 'X', 'Y')

    ...SERVER...

        >>> test('--- welcome to irc.example.org')
        None SERVER '--- welcome to irc.example.org'
        >>> test('*** welcome to irc.example.org')
        None SERVER '*** welcome to irc.example.org'

    All unrecognized lines are reported as OTHER

        >>> test('what is this line doing in my IRC log file?')
        None OTHER 'what is this line doing in my IRC log file?'

    """


def doctest_LogParser_dircproxy_support():
    r"""Tests for LogParser

    I'll define a helper function to test parsing.

        >>> def test(line):
        ...     for time, what, info in LogParser([line], dircproxy=True):
        ...         print(myrepr(time), what, myrepr(info))

        >>> test('[15 Jan 08:42] <mg!n=user@10.0.0.1> -hmm')
        '15 Jan 08:42' COMMENT ('mg', 'hmm')
        >>> test('[15 Jan 08:42] <mg!n=user@10.0.0.1> +this')
        '15 Jan 08:42' COMMENT ('mg', 'this')
        >>> test('[15 Jan 08:42] <mg!n=user@10.0.0.1> maybe')
        '15 Jan 08:42' COMMENT ('mg', 'maybe')
        >>> test('[15 Jan 08:42] <mg!n=user@10.0.0.1> --1')
        '15 Jan 08:42' COMMENT ('mg', '-1')
        >>> test('[15 Jan 08:42] <mg!n=user@10.0.0.1> ++2')
        '15 Jan 08:42' COMMENT ('mg', '+2')
        >>> test('[15 Jan 08:42] <mg!n=user@10.0.0.1> +-3')
        '15 Jan 08:42' COMMENT ('mg', '-3')

    """


def doctest_LogParser_encodings():
    r"""Tests for LogParser

    I'll define a helper function to test parsing.

        >>> def test(line):
        ...     for time, what, info in LogParser([line]):
        ...         print(myrepr(time), what, myrepr(info))

    We accept input that's in UTF-8

        >>> test(b'14:18 <mg> UTF-8: \xc4\x85')
        '14:18' COMMENT ('mg', 'UTF-8: \u0105')

    and fall back to Latin-1 (actually, Windows-1252)

        >>> test(b'14:18 <mg> cp1252: \x9a')
        '14:18' COMMENT ('mg', 'cp1252: \u0161')

    For convenience, Unicode is also accepted

        >>> test(u'14:18 <mg> hello, \u2603')
        '14:18' COMMENT ('mg', 'hello, \u2603')

    """


def doctest_ColourChooser():
    """Test for ColourChooser

        >>> cc = ColourChooser()
        >>> print(cc.choose(0, 0))
        #763e3e
        >>> print(cc.choose(0, 30))
        #763e3e
        >>> print(cc.choose(1, 30))
        #407a40
        >>> print(cc.choose(30, 30))
        #e47878
        >>> print(cc.choose(31, 30))
        #79e779

    """


def doctest_NickColourizer():
    """Test for NickColourizer

        >>> nc = NickColourizer()

    The API provided by NickColourizer is dict-like

        >>> print(nc['mgedmin'])
        #407a40

    Same nick gets the same colour

        >>> print(nc['mgedmin'])
        #407a40

    Different nicks get different colours

        >>> print(nc['povbot'])
        #42427e

    Nick changes keep the old color

        >>> nc.change('mgedmin', 'mg_away')
        >>> print(nc['mg_away'])
        #407a40

    Old nick gets a new color

        >>> print(nc['mgedmin'])
        #818144

    We can handle more than 30 nics

        >>> for nick in range(100):
        ...     assert nc['nick%d' % nick] != ''

    """


class BytesIOWrapper(object):
    charset = 'UTF-8'
    closed = False

    def __init__(self, stream):
        self.stream = stream

    def readable(self):
        return False

    def writable(self):
        return True

    def seekable(self):
        return False

    def flush(self):
        self.stream.flush()

    def write(self, bytestr):
        self.stream.write(bytestr.decode(self.charset))
        self.stream.flush()


def doctest_SimpleTextStyle():
    """Test for SimpleTextStyle

        >>> style = SimpleTextStyle(BytesIOWrapper(sys.stdout))
        >>> style.head('IRC logs of #channel for Monday, 2008-06-10')
        <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
        <html>
        <head>
            <title>IRC logs of #channel for Monday, 2008-06-10</title>
            <meta name="generator" content="irclog2html.py ... by Marius Gedminas">
            <meta name="version" content="...">
            <meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
        </head>
        <body text="#000000" bgcolor="#ffffff"><tt>

        >>> style.nicktext('02:24:17', 'mgedmin', 'Hello, world!', '#77ff77')
        &lt;mgedmin&gt; Hello, world!<br>

        >>> style.nicktext('02:24', 'mgedmin', 'http://google.com/ has a new favicon', '#77ff77')
        &lt;mgedmin&gt; <a href="http://google.com/" rel="nofollow">http://google.com/</a> has a new favicon<br>

        >>> style.servermsg('02:25', LogParser.ACTION, '* mgedmin hacks <&>')
        * mgedmin hacks &lt;&amp;&gt;<br>

        >>> style.servermsg('02:26:01', LogParser.PART, '* mgedmin leaves')
        * mgedmin leaves<br>

        >>> style.foot()
        <BLANKLINE>
        <br>Generated by irclog2html.py ... by <a href="mailto:marius@pov.lt">Marius Gedminas</a>
         - find it at <a href="http://mg.pov.lt/irclog2html/">mg.pov.lt</a>!
        </tt></body></html>

    """


def doctest_SimpleTextStyle_colourful():
    """Test for SimpleTextStyle

        >>> style = SimpleTextStyle(BytesIOWrapper(sys.stdout),
        ...     colours=dict((what, c) for name, c, what in COLOURS))
        >>> style.head('IRC logs of #channel for Monday, 2008-06-10')
        <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
        <html>
        <head>
            <title>IRC logs of #channel for Monday, 2008-06-10</title>
            <meta name="generator" content="irclog2html.py ... by Marius Gedminas">
            <meta name="version" content="...">
            <meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
        </head>
        <body text="#000000" bgcolor="#ffffff"><tt>

        >>> style.nicktext('02:24:17', 'mgedmin', 'Hello, world!', '#77ff77')
        &lt;mgedmin&gt; Hello, world!<br>

        >>> style.nicktext('02:24', 'mgedmin', 'http://google.com/ has a new favicon', '#77ff77')
        &lt;mgedmin&gt; <a href="http://google.com/" rel="nofollow">http://google.com/</a> has a new favicon<br>

        >>> style.servermsg('02:25', LogParser.ACTION, '* mgedmin hacks <&>')
        <font color="#CC00CC">* mgedmin hacks &lt;&amp;&gt;</font><br>

        >>> style.servermsg('02:26:01', LogParser.PART, '* mgedmin leaves')
        <font color="#000099">* mgedmin leaves</font><br>

        >>> style.foot()
        <BLANKLINE>
        <br>Generated by irclog2html.py ... by <a href="mailto:marius@pov.lt">Marius Gedminas</a>
         - find it at <a href="http://mg.pov.lt/irclog2html/">mg.pov.lt</a>!
        </tt></body></html>

    """


def doctest_TextStyle_colourful():
    """Test for TextStyle

        >>> style = TextStyle(BytesIOWrapper(sys.stdout),
        ...     colours=dict((what, c) for name, c, what in COLOURS))
        >>> style.head('IRC logs of #channel for Monday, 2008-06-10')
        <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
        <html>
        <head>
            <title>IRC logs of #channel for Monday, 2008-06-10</title>
            <meta name="generator" content="irclog2html.py ... by Marius Gedminas">
            <meta name="version" content="...">
            <meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
        </head>
        <body text="#000000" bgcolor="#ffffff"><tt>

        >>> style.nicktext('02:24:17', 'mgedmin', 'Hello, world!', '#77ff77')
        <font color="#77ff77">&lt;mgedmin&gt;</font> <font color="#000000">Hello, world!</font><br>

        >>> style.nicktext('02:24', 'mgedmin', 'http://google.com/ has a new favicon', '#77ff77')
        <font color="#77ff77">&lt;mgedmin&gt;</font> <font color="#000000"><a href="http://google.com/" rel="nofollow">http://google.com/</a> has a new favicon</font><br>

        >>> style.servermsg('02:25', LogParser.ACTION, '* mgedmin hacks <&>')
        <font color="#CC00CC">* mgedmin hacks &lt;&amp;&gt;</font><br>

        >>> style.servermsg('02:26:01', LogParser.PART, '* mgedmin leaves')
        <font color="#000099">* mgedmin leaves</font><br>

        >>> style.foot()
        <BLANKLINE>
        <br>Generated by irclog2html.py ... by <a href="mailto:marius@pov.lt">Marius Gedminas</a>
         - find it at <a href="http://mg.pov.lt/irclog2html/">mg.pov.lt</a>!
        </tt></body></html>

    """


def doctest_SimpleTableStyle():
    """Test for SimpleTableStyle

        >>> style = SimpleTableStyle(BytesIOWrapper(sys.stdout))
        >>> style.head('IRC logs of #channel for Monday, 2008-06-10')
        <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
        <html>
        <head>
           <title>IRC logs of #channel for Monday, 2008-06-10</title>
            <meta name="generator" content="irclog2html.py ... by Marius Gedminas">
            <meta name="version" content="...">
            <meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
        </head>
        <body text="#000000" bgcolor="#ffffff"><tt>
        <table cellspacing=3 cellpadding=2 border=0>

        >>> style.nicktext('02:24:17', 'mgedmin', 'Hello, world!', '#77ff77')
        <tr bgcolor="#eeeeee"><th><font color="#77ff77"><tt>mgedmin</tt></font></th><td width="100%"><tt>Hello, world!</tt></td></tr>

        >>> style.nicktext('02:24', 'mgedmin', 'http://google.com/ has a new favicon', '#77ff77')
        <tr bgcolor="#eeeeee"><th><font color="#77ff77"><tt>mgedmin</tt></font></th><td width="100%"><tt><a href="http://google.com/" rel="nofollow">http://google.com/</a> has a new favicon</tt></td></tr>

        >>> style.servermsg('02:25', LogParser.ACTION, '* mgedmin hacks <&>')
        <tr><td colspan=2><tt>* mgedmin hacks &lt;&amp;&gt;</tt></td></tr>

        >>> style.servermsg('02:26:01', LogParser.PART, '* mgedmin leaves')
        <tr><td colspan=2><tt>* mgedmin leaves</tt></td></tr>

        >>> style.foot()
        </table>
        <BLANKLINE>
        <br>Generated by irclog2html.py ... by <a href="mailto:marius@pov.lt">Marius Gedminas</a>
         - find it at <a href="http://mg.pov.lt/irclog2html/">mg.pov.lt</a>!
        </tt></body></html>

    """


def doctest_TableStyle():
    """Test for TableStyle

        >>> style = TableStyle(BytesIOWrapper(sys.stdout))
        >>> style.head('IRC logs of #channel for Monday, 2008-06-10')
        <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
        <html>
        <head>
           <title>IRC logs of #channel for Monday, 2008-06-10</title>
            <meta name="generator" content="irclog2html.py ... by Marius Gedminas">
            <meta name="version" content="...">
            <meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
        </head>
        <body text="#000000" bgcolor="#ffffff"><tt>
        <table cellspacing=3 cellpadding=2 border=0>

        >>> style.nicktext('02:24:17', 'mgedmin', 'Hello, world!', '#77ff77')
        <tr><th bgcolor="#77ff77"><font color="#ffffff"><tt>mgedmin</tt></font></th><td width="100%" bgcolor="#eeeeee"><tt><font color="#77ff77">Hello, world!</font></tt></td></tr>

        >>> style.nicktext('02:24', 'mgedmin', 'http://google.com/ has a new favicon', '#77ff77')
        <tr><th bgcolor="#77ff77"><font color="#ffffff"><tt>mgedmin</tt></font></th><td width="100%" bgcolor="#eeeeee"><tt><font color="#77ff77"><a href="http://google.com/" rel="nofollow">http://google.com/</a> has a new favicon</font></tt></td></tr>

        >>> style.servermsg('02:25', LogParser.ACTION, '* mgedmin hacks <&>')
        <tr><td colspan=2><tt>* mgedmin hacks &lt;&amp;&gt;</tt></td></tr>

        >>> style.servermsg('02:26:01', LogParser.PART, '* mgedmin leaves')
        <tr><td colspan=2><tt>* mgedmin leaves</tt></td></tr>

        >>> style.foot()
        </table>
        <BLANKLINE>
        <br>Generated by irclog2html.py ... by <a href="mailto:marius@pov.lt">Marius Gedminas</a>
         - find it at <a href="http://mg.pov.lt/irclog2html/">mg.pov.lt</a>!
        </tt></body></html>

    """


def doctest_XHTMLStyle():
    """Test for XHTMLStyle

        >>> style = XHTMLStyle(BytesIOWrapper(sys.stdout))
        >>> style.head('IRC logs of #channel for Monday, 2008-06-10')
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
                  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
        <html>
        <head>
          <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
          <title>IRC logs of #channel for Monday, 2008-06-10</title>
          <link rel="stylesheet" href="irclog.css" />
          <meta name="generator" content="irclog2html.py ... by Marius Gedminas" />
          <meta name="version" content="..." />
        </head>
        <body>
        <h1>IRC logs of #channel for Monday, 2008-06-10</h1>
        <div class="irclog">

        >>> style.nicktext('02:24:17', 'mgedmin', 'Hello, world!', '#77ff77')
        <p id="t02:24:17" class="comment"><a href="#t02:24:17" class="time">02:24</a> <span class="nick" style="color: #77ff77">&lt;mgedmin&gt;</span> <span class="text">Hello, world!</span></p>

        >>> style.nicktext('02:24', 'mgedmin', 'http://google.com/ has a new favicon', '#77ff77')
        <p id="t02:24" class="comment"><a href="#t02:24" class="time">02:24</a> <span class="nick" style="color: #77ff77">&lt;mgedmin&gt;</span> <span class="text"><a href="http://google.com/" rel="nofollow">http://google.com/</a> has a new favicon</span></p>

        >>> style.servermsg('02:25', LogParser.ACTION, '* mgedmin hacks <&>')
        <p id="t02:25" class="action"><a href="#t02:25" class="time">02:25</a> * mgedmin hacks &lt;&amp;&gt;</p>

        >>> style.servermsg('02:25', LogParser.ACTION, '* mgedmin is very fast')
        <p id="t02:25-2" class="action"><a href="#t02:25-2" class="time">02:25</a> * mgedmin is very fast</p>

        >>> style.servermsg('02:26:01', LogParser.PART, '* mgedmin leaves')
        <p id="t02:26:01" class="part"><a href="#t02:26:01" class="time">02:26</a> * mgedmin leaves</p>

        >>> style.nicktext(None, 'mgedmin', 'what time is it?', '#77ff77')
        <p class="comment"><span class="nick" style="color: #77ff77">&lt;mgedmin&gt;</span> <span class="text">what time is it?</span></p>

        >>> style.servermsg(None, LogParser.PART, '* wombat leaves')
        <p class="part">* wombat leaves</p>

        >>> style.foot()
        </div>
        <BLANKLINE>
        <div class="generatedby">
        <p>Generated by irclog2html.py ... by <a href="mailto:marius@pov.lt">Marius Gedminas</a>
         - find it at <a href="http://mg.pov.lt/irclog2html/">mg.pov.lt</a>!</p>
        </div>
        </body>
        </html>

    """


def doctest_XHTMLStyle_with_navigation_and_searchbox():
    """Test for XHTMLStyle

        >>> style = XHTMLStyle(BytesIOWrapper(sys.stdout))
        >>> style.head('IRC logs of #channel for Monday, 2008-06-10',
        ...            searchbox=True,
        ...            prev=('Prev', 'prev.html'),
        ...            next=('Next', None),
        ...            index=('Index', 'index.html'))
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
                  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
        <html>
        <head>
          <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
          <title>IRC logs of #channel for Monday, 2008-06-10</title>
          <link rel="stylesheet" href="irclog.css" />
          <meta name="generator" content="irclog2html.py ... by Marius Gedminas" />
          <meta name="version" content="..." />
        </head>
        <body>
        <h1>IRC logs of #channel for Monday, 2008-06-10</h1>
        <BLANKLINE>
        <div class="searchbox">
        <form action="search" method="get">
        <input type="text" name="q" id="searchtext" />
        <input type="submit" value="Search" id="searchbutton" />
        </form>
        </div>
        <BLANKLINE>
        <div class="navigation"> <a href="prev.html">Prev</a> <a href="index.html">Index</a> <span class="disabled">Next</span> </div>
        <div class="irclog">

    """


def doctest_XHTMLTableStyle():
    """Test for XHTMLTableStyle

        >>> style = XHTMLTableStyle(BytesIOWrapper(sys.stdout))
        >>> style.head('IRC logs of #channel for Monday, 2008-06-10')
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
                  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
        <html>
        <head>
          <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
          <title>IRC logs of #channel for Monday, 2008-06-10</title>
          <link rel="stylesheet" href="irclog.css" />
          <meta name="generator" content="irclog2html.py ... by Marius Gedminas" />
          <meta name="version" content="..." />
        </head>
        <body>
        <h1>IRC logs of #channel for Monday, 2008-06-10</h1>
        <table class="irclog">

        >>> style.nicktext('02:24:17', 'mgedmin', 'Hello, world!', '#77ff77')
        <tr id="t02:24:17"><th class="nick" style="background: #77ff77">mgedmin</th><td class="text" style="color: #77ff77">Hello, world!</td><td class="time"><a href="#t02:24:17" class="time">02:24</a></td></tr>

        >>> style.nicktext('02:24', 'mgedmin', 'http://google.com/ has a new favicon', '#77ff77')
        <tr id="t02:24"><th class="nick" style="background: #77ff77">mgedmin</th><td class="text" style="color: #77ff77"><a href="http://google.com/" rel="nofollow">http://google.com/</a> has a new favicon</td><td class="time"><a href="#t02:24" class="time">02:24</a></td></tr>

        >>> style.servermsg('02:25', LogParser.ACTION, '* mgedmin hacks <&>')
        <tr id="t02:25"><td class="action" colspan="2">* mgedmin hacks &lt;&amp;&gt;</td><td><a href="#t02:25" class="time">02:25</a></td></tr>

        >>> style.servermsg('02:26:01', LogParser.PART, '* mgedmin leaves')
        <tr id="t02:26:01"><td class="part" colspan="2">* mgedmin leaves</td><td><a href="#t02:26:01" class="time">02:26</a></td></tr>

        >>> style.nicktext(None, 'mgedmin', 'what time is it?', '#77ff77')
        <tr><th class="nick" style="background: #77ff77">mgedmin</th><td class="text" colspan="2" style="color: #77ff77">what time is it?</td></tr>

        >>> style.servermsg(None, LogParser.PART, '* wombat leaves')
        <tr><td class="part" colspan="3">* wombat leaves</td></tr>

        >>> style.foot()
        </table>
        <BLANKLINE>
        <div class="generatedby">
        <p>Generated by irclog2html.py ... by <a href="mailto:marius@pov.lt">Marius Gedminas</a>
         - find it at <a href="http://mg.pov.lt/irclog2html/">mg.pov.lt</a>!</p>
        </div>
        </body>
        </html>

    """


def doctest_MediaWikiStyle():
    r"""Tests for MediaWikiStyle

        >>> style = MediaWikiStyle(BytesIOWrapper(sys.stdout))

    The heading is trivial

        >>> style.head('IRC logs of #channel for Monday, 2008-06-10')
        {|

    We may have simple messages

        >>> style.nicktext('02:24:17', 'mgedmin', 'Hello, world!', '#77ff77')
        |- id="t02:24:17"
        ! style="background-color: #77ff77" | mgedmin
        | style="color: #77ff77" | Hello, world!
        || [[#t02:24:17|02:24]]

    Note that we don't need special markup for hyperlinks

        >>> style.nicktext('02:24', 'mgedmin', 'http://google.com/ has a new favicon', '#77ff77')
        |- id="t02:24"
        ! style="background-color: #77ff77" | mgedmin
        | style="color: #77ff77" | http://google.com/ has a new favicon
        || [[#t02:24|02:24]]

    But we ought to escape MediaWiki markup (XXX this is not currently done,
    would someone familiar with the markup please fix the code)

        >>> style.nicktext('02:24', '[|mg|]', '[!@#$%^&*()_+{};:,./<>?]', '#77ff77')
        |- id="t02:24"
        ! style="background-color: #77ff77" | [|mg|]
        | style="color: #77ff77" | [!@#$%^&amp;*()_+{};:,./&lt;&gt;?]
        || [[#t02:24|02:24]]

    The time is optional (some IRC logs don't have it)

        >>> style.nicktext(None, 'mgedmin', 'what time is it?', '#77ff77')
        |-
        | style="background-color: #77ff77" | mgedmin
        | style="color: #77ff77" colspan="2" | what time is it?

    There are other kinds of things that happen in IRC channels

        >>> style.servermsg('02:25', LogParser.ACTION, '* mgedmin hacks')
        |- id="t02:25"
        | colspan="2" | * mgedmin hacks
        || [[#t02:25|02:25]]

        >>> style.servermsg('02:26:01', LogParser.PART, '* mgedmin leaves')
        |- id="t02:26:01"
        | colspan="2" | * mgedmin leaves
        || [[#t02:26:01|02:26]]

    The time is optional (some IRC logs don't have it)

        >>> style.servermsg(None, LogParser.JOIN, '* wombat joins')
        |-
        | colspan="3" | * wombat joins

    Again, we ought to escape MediaWiki markup (XXX this is not currently
    done, would someone familiar with the markup please fix the code)

        >>> style.servermsg(None, LogParser.SERVER, '[!@#$%^&*()_+{};:,./<>?]')
        |-
        | colspan="3" | [!@#$%^&amp;*()_+{};:,./&lt;&gt;?]

    The footer is also simple

        >>> style.foot()
        |}
        <BLANKLINE>
        Generated by irclog2html.py ... by [mailto:marius@pov.lt Marius Gedminas] - find it at [http://mg.pov.lt/irclog2html mg.pov.lt]!

    """


def run(*args):
    stderr = sys.stderr
    try:
        sys.stderr = sys.stdout
        main(['irclog2html'] + list(args))
    except SystemExit as e:
        if e.args[0] != 0:
            print("SystemExit(%s)" % myrepr(e.args[0]))
    finally:
        sys.stderr = stderr


def doctest_main_can_show_help():
    """Test for main

        >>> run('--help')
        Usage: irclog2html [options] filename [...]
        <BLANKLINE>
        Colourises and converts IRC logs to HTML format for easy web reading.
        <BLANKLINE>
        Options:
          --version             show program's version number and exit
          -h, --help            show this help message and exit
        ...
          --color-action=COLOUR_ACTION, --colour-action=COLOUR_ACTION
                                select action colour (default: #CC00CC)

    """


def doctest_main_can_list_styles():
    """Test for main

        >>> run('--style', 'help')
        The following styles are available for use with irclog2html.py:
        <BLANKLINE>
          simplett
            Text style with little use of colour
        ...

    """


def doctest_main_can_handle_unknown_style():
    """Test for main

        >>> run('--style', 'nosuchstyle')
        Usage: irclog2html [options] filename [...]
        <BLANKLINE>
        irclog2html: error: unknown style: nosuchstyle
        SystemExit(2)

    """


def doctest_main_can_read_config_file():
    """Test for main

        >>> fn = os.path.join(here, 'sample.cfg')
        >>> parser, options, args = parse_args(['irclog2html', '--config', fn])
        >>> options.title
        'IRC logs for #mychannel'
        >>> options.searchbox
        True

    """


def doctest_main_can_handle_input_errors():
    """Test for main

        >>> run('/no/such/file')
        SystemExit("irclog2html: cannot open /no/such/file for reading: [Errno 2] No such file or directory: '/no/such/file'")

    """


def doctest_main():
    """Test for main

        >>> tmpdir = tempfile.mkdtemp(prefix='irclog2html-test-')
        >>> fn = os.path.join(tmpdir, 'sample.log')
        >>> _ = shutil.copyfile(os.path.join(here, 'sample.log'), fn)
        >>> run(fn)
        >>> with io.open(fn + '.html', encoding='UTF-8') as f:
        ...     print(f.read())
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
                  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
        ...
        >>> shutil.rmtree(tmpdir)

    """


def doctest_main_can_handle_output_errors():
    """Test for main

        >>> tmpdir = tempfile.mkdtemp(prefix='irclog2html-test-')
        >>> _ = shutil.copyfile(os.path.join(here, 'sample.log'),
        ...                     os.path.join(tmpdir, 'sample.log'))
        >>> outfilename = os.path.join(tmpdir, 'sample.log.html')
        >>> open(outfilename, 'w').close()
        >>> os.chmod(outfilename, 0o444)
        >>> run(os.path.join(tmpdir, 'sample.log'))
        SystemExit("irclog2html: cannot open ...sample.log.html for writing: [Errno 13] Permission denied: ...sample.log.html'")
        >>> os.chmod(outfilename, 0o644)
        >>> shutil.rmtree(tmpdir)

    """


def doctest_main_can_handle_missing_config_file():
    """Test for main

        >>> run('--config', '/no/such/file')
        Usage: irclog2html [options] filename [...]
        <BLANKLINE>
        irclog2html: error: can't read config file: [Errno 2] No such file or directory: '/no/such/file'
        SystemExit(2)

    """


def doctest_main_can_handle_missing_file():
    """Test for main

        >>> run('--style', 'tt', '--colour-action', 'red')
        Usage: irclog2html [options] filename [...]
        <BLANKLINE>
        irclog2html: error: please specify a filename
        SystemExit(2)

    """


def doctest_main_complains_if_single_output_file_for_multiple_input_files_is_given():
    """Test for main

        >>> run('chan1.log', 'chan2.log', '-o', 'output.html')
        Usage: irclog2html [options] filename [...]
        <BLANKLINE>
        irclog2html: error: -o must be a directory when processing multiple files
        SystemExit(2)

    """


def doctest_main_output_file():
    """Test for main

        >>> tmpdir = tempfile.mkdtemp(prefix='irclog2html-test-')
        >>> fn = os.path.join(here, 'sample.log')
        >>> outfn = os.path.join(tmpdir, 'output.html')
        >>> run(fn, '-o', outfn)
        >>> with io.open(outfn, encoding='UTF-8') as f:
        ...     print(f.read())
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
                  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
        ...
        >>> shutil.rmtree(tmpdir)

    """


def doctest_main_output_directory():
    """Test for main

        >>> tmpdir = tempfile.mkdtemp(prefix='irclog2html-test-')
        >>> fn = os.path.join(here, 'sample.log')
        >>> run(fn, '-o', tmpdir)
        >>> outfn = os.path.join(tmpdir, 'sample.log.html')
        >>> with io.open(outfn, encoding='UTF-8') as f:
        ...     print(f.read())
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
                  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
        ...
        >>> shutil.rmtree(tmpdir)

    """


def test_suite():
    optionflags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS | doctest.REPORT_NDIFF
    return unittest.TestSuite([
        doctest.DocTestSuite('irclog2html.irclog2html'),
        doctest.DocTestSuite(optionflags=optionflags),
    ])
