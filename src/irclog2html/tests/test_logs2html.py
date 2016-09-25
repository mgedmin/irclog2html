import datetime
import doctest
import os
import time
import shutil
import sys
import tempfile
import unittest
import optparse

from irclog2html.logs2html import (
    Error, LogFile, find_log_files, write_index, process, move_symlink,
    main)


class TestCase(unittest.TestCase):

    def setUp(self):
        self.tmpdir = None
        self.start_time = time.time()

    def tearDown(self):
        if self.tmpdir:
            try:
                shutil.rmtree(self.tmpdir)
            except Exception as e:
                sys.stderr.write(
                    "\nAn error happened while cleaning up %s:\n%s: %s\n"
                    % (self.tmpdir, e.__class__.__name__, e))
                sys.stderr.flush()

    def filename(self, filename):
        if self.tmpdir is None:
            self.tmpdir = tempfile.mkdtemp(prefix='irclog2html-test-')
        return os.path.join(self.tmpdir, filename)

    def create(self, filename, mtime=None):
        fullfilename = self.filename(filename)
        with open(fullfilename, 'w'):
            pass
        if mtime:
            mtime += self.start_time
            os.utime(fullfilename, (mtime, mtime))


class TestLogFile(TestCase):

    def LogFile(self, filename):
        return LogFile(self.filename(filename))

    def test_with_date(self):
        # no need to create temporary files for this test, so don't use
        # self.LogFile
        lf = LogFile('/path/to/somechannel-20130318.log')
        self.assertEqual(lf.date, datetime.date(2013, 3, 18))
        self.assertEqual(lf.link, 'somechannel-20130318.log.html')
        self.assertEqual(lf.title, '2013-03-18 (Monday)')

    def test_without_date(self):
        # no need to create temporary files for this test, so don't use
        # self.LogFile
        self.assertRaises(Error, LogFile, '/path/to/somechannel.log')

    def test_equality(self):
        lf1 = LogFile('/path/to/somechannel-20130318.log')
        lf2 = LogFile('/path/to/somechannel-20130319.log')
        lf3 = LogFile('/path/to/somechannel-20130318.log')
        self.assertEqual(lf1, lf1)
        self.assertEqual(lf1, lf3)
        self.assertNotEqual(lf1, lf2)

    def test_newfile_html_exists(self):
        self.create('somechannel-20130317.log')
        self.create('somechannel-20130317.log.html')
        lf = self.LogFile('somechannel-20130317.log')
        self.assertFalse(lf.newfile())

    def test_newfile_html_doesnt_exist(self):
        self.create('somechannel-20130318.log')
        lf = self.LogFile('somechannel-20130318.log')
        self.assertTrue(lf.newfile())

    def test_uptodate_html_doesnt_exist(self):
        self.create('somechannel-20130317.log')
        lf = self.LogFile('somechannel-20130317.log')
        self.assertFalse(lf.uptodate())

    def test_uptodate_html_is_newer(self):
        self.create('somechannel-20130317.log', mtime=-100)
        self.create('somechannel-20130317.log.html', mtime=-50)
        lf = self.LogFile('somechannel-20130317.log')
        self.assertTrue(lf.uptodate())

    def test_uptodate_html_is_older(self):
        self.create('somechannel-20130317.log', mtime=-10)
        self.create('somechannel-20130317.log.html', mtime=-50)
        lf = self.LogFile('somechannel-20130317.log')
        self.assertFalse(lf.uptodate())

    def test_uptodate_html_is_same_age(self):
        self.create('somechannel-20130317.log', mtime=-10)
        self.create('somechannel-20130317.log.html', mtime=-10)
        lf = self.LogFile('somechannel-20130317.log')
        self.assertFalse(lf.uptodate()) # err on the safe side: regenerate

    def test_generate(self):
        self.create('somechannel-20130317.log')
        lf = self.LogFile('somechannel-20130317.log')
        lf.generate(style='tt')
        outfile = self.filename('somechannel-20130317.log.html')
        self.assertTrue(os.path.exists(outfile))

    def test_generate_with_navbar(self):
        self.create('somechannel-20130317.log')
        prev = self.LogFile('somechannel-20130316.log')
        lf = self.LogFile('somechannel-20130317.log')
        next = self.LogFile('somechannel-20130318.log')
        lf.generate(style='tt', prev=prev, next=next)
        outfile = self.filename('somechannel-20130317.log.html')
        self.assertTrue(os.path.exists(outfile))

    def test_find_log_files(self):
        self.create('somechannel-20130316.log')
        self.create('somechannel-20130316.log.html')
        self.create('somechannel-20130317.log')
        self.create('somechannel-20130318.log')
        self.assertEqual(find_log_files(self.tmpdir),
                         [self.LogFile('somechannel-20130316.log'),
                          self.LogFile('somechannel-20130317.log'),
                          self.LogFile('somechannel-20130318.log')])

    def test_move_symlink(self):
        if not hasattr(os, 'symlink'):
            if not hasattr(self, 'skipTest'): # Python 2.6
                return
            self.skipTest("platform does not support symlinks")
        move_symlink('somechannel-20130316.log.html',
                     self.filename('latest.log.html'))
        self.assertEqual(os.readlink(self.filename('latest.log.html')),
                         'somechannel-20130316.log.html')
        move_symlink('somechannel-20130317.log.html',
                     self.filename('latest.log.html'))
        self.assertEqual(os.readlink(self.filename('latest.log.html')),
                         'somechannel-20130317.log.html')

    def test_process(self):
        self.create('somechannel-20130316.log')
        self.create('somechannel-20130316.log.html')
        self.create('somechannel-20130317.log')
        self.create('somechannel-20130318.log')
        options = optparse.Values(dict(searchbox=True, dircproxy=True,
                                       pattern='*.log', force=False,
                                       prefix='IRC logs for ',
                                       style='xhtmltable', title='IRC logs'))
        process(self.tmpdir, options)
        self.assertTrue(os.path.exists(self.filename('index.html')))
        if hasattr(os, 'symlink'):
            self.assertTrue(os.path.exists(self.filename('latest.log.html')))
        self.assertTrue(os.path.exists(self.filename('irclog.css')))
        self.assertTrue(os.path.exists(
            self.filename('somechannel-20130316.log.html')))
        self.assertTrue(os.path.exists(
            self.filename('somechannel-20130317.log.html')))
        self.assertTrue(os.path.exists(
            self.filename('somechannel-20130318.log.html')))

    def test_process_copies_css_even_when_all_logs_up_to_date(self):
        self.create('somechannel-20130316.log', mtime=-10)
        self.create('somechannel-20130316.log.html')
        options = optparse.Values(dict(searchbox=True, dircproxy=True,
                                       pattern='*.log', force=False,
                                       prefix='IRC logs for ',
                                       style='xhtmltable', title='IRC logs'))
        process(self.tmpdir, options)
        self.assertTrue(os.path.exists(self.filename('index.html')))
        if hasattr(os, 'symlink'):
            self.assertTrue(os.path.exists(self.filename('latest.log.html')))
        self.assertTrue(os.path.exists(self.filename('irclog.css')))

    def test_process_handles_write_errors(self):
        self.create('somechannel-20130316.log', mtime=-10)
        self.create('somechannel-20130316.log.html')
        self.create('index.html')
        options = optparse.Values(dict(searchbox=True, dircproxy=True,
                                       pattern='*.log', force=False,
                                       prefix='IRC logs for ',
                                       style='xhtmltable', title='IRC logs'))
        os.chmod(self.filename('index.html'), 0o444)
        self.assertRaises(Error, process, self.tmpdir, options)
        # shutil.rmtree() on Windows can't handle read-only files.
        # Restore the permissions so that our tearDown() can succeed.
        os.chmod(self.filename('index.html'), 0o644)

    def test_main(self):
        self.create('somechannel-20130316.log')
        self.create('somechannel-20130316.log.html')
        self.create('somechannel-20130317.log')
        self.create('somechannel-20130318.log')
        main(['logs2html', self.tmpdir])
        self.assertTrue(os.path.exists(self.filename('index.html')))
        if hasattr(os, 'symlink'):
            self.assertTrue(os.path.exists(self.filename('latest.log.html')))
        self.assertTrue(os.path.exists(self.filename('irclog.css')))
        self.assertTrue(os.path.exists(
            self.filename('somechannel-20130316.log.html')))
        self.assertTrue(os.path.exists(
            self.filename('somechannel-20130317.log.html')))
        self.assertTrue(os.path.exists(
            self.filename('somechannel-20130318.log.html')))

    def test_main_error_handling(self):
        self.create('nodate.log')
        self.assertRaises(SystemExit, main, ['logs2html', self.tmpdir])


def doctest_write_index():
    """Test for write_index

        >>> write_index(sys.stdout,
        ...             title='IRC logs for somechannel',
        ...             logfiles=[LogFile('somechannel-20130316.log'),
        ...                       LogFile('somechannel-20130317.log'),
        ...                       LogFile('somechannel-20130318.log')],
        ...             latest_log_link='latest.html')
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
                  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
        <html>
        <head>
          <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
          <title>IRC logs for somechannel</title>
          <link rel="stylesheet" href="irclog.css" />
          <meta name="generator" content="logs2html.py ... by Marius Gedminas" />
          <meta name="version" content="..." />
        </head>
        <body>
        <h1>IRC logs for somechannel</h1>
        <ul>
        <li><a href="latest.html">Latest (bookmarkable)</a></li>
        </ul>
        <ul>
        </ul>
        <h2>2013-03</h2>
        <ul>
        <li><a href="somechannel-20130316.log.html">2013-03-16 (Saturday)</a></li>
        <li><a href="somechannel-20130317.log.html">2013-03-17 (Sunday)</a></li>
        <li><a href="somechannel-20130318.log.html">2013-03-18 (Monday)</a></li>
        </ul>
        <BLANKLINE>
        <div class="generatedby">
        <p>Generated by logs2html.py ... by <a href="mailto:marius@pov.lt">Marius Gedminas</a>
         - find it at <a href="http://mg.pov.lt/irclog2html/">mg.pov.lt</a>!</p>
        </div>
        </body>
        </html>

    """


def run(*args):
    stderr = sys.stderr
    try:
        sys.stderr = sys.stdout
        main(['logs2html'] + list(args))
    except SystemExit as e:
        if e.args[0] != 0:
            print("SystemExit(%s)" % repr(e.args[0]))
    finally:
        sys.stderr = stderr


def doctest_main_can_print_help():
    """Test for main

        >>> run('--help')
        Usage: logs2html [options] directory
        <BLANKLINE>
        Colourises and converts all IRC logs to HTML format for easy web reading.
        <BLANKLINE>
        Options:
          --version             show program's version number and exit
          -h, --help            show this help message and exit
          ...

    """


def doctest_main_missing_dirname():
    """Test for main

        >>> run('--style', 'tt')
        Usage: logs2html [options] directory
        <BLANKLINE>
        logs2html: error: missing directory name
        SystemExit(2)

    """


def doctest_main_extra_args():
    """Test for main

        >>> run('dir1', 'dir2')
        Usage: logs2html [options] directory
        <BLANKLINE>
        logs2html: error: too many arguments
        SystemExit(2)

    """


def test_suite():
    return unittest.TestSuite([
        doctest.DocTestSuite(optionflags=doctest.ELLIPSIS | doctest.REPORT_NDIFF),
        unittest.makeSuite(TestLogFile),
    ])
