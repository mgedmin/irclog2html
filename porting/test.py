#!/usr/bin/env python
"""
Functional tests for irclog2html.py

You must run this script in a directory that contains irclog2html.py,
irclog2html.pl and testcases/*.log.  Both scripts must be executable.
"""
import os
import tempfile
import shutil
import difflib
import glob

from irclog2html import VERSION, RELEASE


def replace(s, replacements):
    """Replace a bunch of things in a string."""
    replacements = [(-len(k), k, v) for k, v in replacements.iteritems()]
    replacements.sort() # longest first
    for sortkey, k, v in replacements:
        s = s.replace(k, v)
    return s


def run_in_tempdir(inputfile, script, args):
    """Copy inputfile into a temporary directory and run a given command.

    Arguments for the script are args with the name of the copied file
    appended (e.g. run('/var/log/irc.log', 'irclog2html.py', '-s table')
    will run irclog2html.py -s table /tmp/tempdirname/irc.log)

    Performs no shell escaping whatsoever.

    Returns the contents of the output file (inputfile + '.html' in the
    temporary directory).
    """
    dir = tempfile.mkdtemp()
    try:
        newinputfile = os.path.join(dir, os.path.basename(inputfile))
        shutil.copyfile(inputfile, newinputfile)
        cmdline = '%s %s %s' % (script, args, newinputfile)
        pipe = os.popen('%s 2>&1' % cmdline, 'r')
        output = pipe.read()
        status = pipe.close()
        if status:
            raise AssertionError('%s returned status code %s\n%s'
                                 % (cmdline, status, output))
        if output:
            raise AssertionError('%s said\n%s'
                                 % (cmdline, output))
        outfilename = newinputfile + '.html'
        try:
            return open(outfilename).read().replace(dir, '/tmpdir')
        except IOError, e:
            raise AssertionError('%s did not create the output file\n%s' %
                                 (cmdline, e))
    finally:
        shutil.rmtree(dir)


def run_and_compare(inputfile, args=""):
    """Run irclog2html.pl and irclog2html.py on inputfile and compare outputs.

    args specify additional command line arguments.
    """
    output1 = run_in_tempdir(inputfile, './irclog2html.py', args)
    output1 = replace(output1, {'irclog2html.py': 'SCRIPT',
                                'Marius Gedminas': 'AUTHOR',
                                VERSION: 'VERSION',
                                RELEASE: 'REVISION',
                                'marius@pov.lt': 'EMAIL',
                                'http://mg.pov.lt/irclog2html/': 'URL',
                                'mg.pov.lt': 'WEBSITE'})
    output2 = run_in_tempdir(inputfile, './irclog2html.pl', args)
    output2 = replace(output2, {'irclog2html.pl': 'SCRIPT',
                                'Jeff Waugh': 'AUTHOR',
                                '2.1mg': 'VERSION',
                                '27th July, 2001': 'REVISION',
                                'jdub@NOSPAMperkypants.org': 'EMAIL',
                                'http://freshmeat.net/projects/irclog2html.pl/':
                                    'URL',
                                'freshmeat.net': 'WEBSITE'})
    if output1 != output2:
        raise AssertionError('files differ (- irclog2html.py,'
                             ' + irclog2html.pl):\n' +
                             ''.join(difflib.ndiff(output1.splitlines(True),
                                                   output2.splitlines(True))))


DEFAULT_ARGS = ('-s table', '-s simplett', '-s tt', '-s simpletable',
                '-s table --colour-part="#deadbe"',
                '-s table --color-action=#cafeba')


def testcase(inputfile, args_to_try=DEFAULT_ARGS):
    """Run both scripts on inputfile with various arguments."""
    print inputfile,
    try:
        for args in args_to_try:
            print ".",
            run_and_compare(inputfile, args)
    except AssertionError, e:
        print "FAILED"
        print
        print e
        print
    else:
        print "ok"


def main():
    os.chdir(os.path.dirname(__file__))
    # the Perl script takes ages to process dircproxy-example.log; ignore it
    testcases = glob.glob('testcases/test*.log')
    print "Comparing outputs produced by the Perl version and the Python port"
    print "There are %d test cases" % len(testcases)
    n = 0
    for inputfile in testcases:
        n += 1
        print n,
        testcase(inputfile)


if __name__ == '__main__':
    main()
