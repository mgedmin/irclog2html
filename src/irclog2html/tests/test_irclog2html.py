#!/usr/bin/env python

import sys
import unittest
import doctest

from irclog2html.irclog2html import LogParser, MediaWikiStyle


def doctest_LogParser():
    r"""Tests for LogParser

    I'll define a helper function to test parsing.

        >>> def test(line):
        ...     for time, what, info in LogParser([line]):
        ...         print repr(time), what, repr(info)

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
        ...         print repr(time), what, repr(info)

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
        ...         print repr(time), what, repr(info)

        >>> test('14:18 <mg> UTF-8: \xc4\x85')
        '14:18' COMMENT ('mg', u'UTF-8: \u0105')

        >>> test('14:18 <mg> cp1252: \x9a')
        '14:18' COMMENT ('mg', u'cp1252: \u0161')

    """


def doctest_MediaWikiStyle():
    r"""Tests for MediaWikiStyle

        >>> style = MediaWikiStyle(sys.stdout)

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

        >>> style.foot()                # doctest: +ELLIPSIS
        |}
        <BLANKLINE>
        Generated by irclog2html.py ... by [mailto:marius@pov.lt Marius Gedminas] - find it at [http://mg.pov.lt/irclog2html mg.pov.lt]!

    """


def test_suite():
    return unittest.TestSuite([
                doctest.DocTestSuite('irclog2html.irclog2html'),
                doctest.DocTestSuite()])

def main():
    unittest.main(defaultTest='test_suite')


if __name__ == '__main__':
    main()
