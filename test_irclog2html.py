#!/usr/bin/env python

def doctest_LogParser():
    r"""Tests for LogParser

    I'll define a helper function to test parsing.

        >>> from irclog2html import LogParser
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


def main():
    import unittest, doctest, irclog2html
    suite = unittest.TestSuite([
                doctest.DocTestSuite(irclog2html),
                doctest.DocTestSuite()])
    unittest.TextTestRunner().run(suite)


if __name__ == '__main__':
    main()
