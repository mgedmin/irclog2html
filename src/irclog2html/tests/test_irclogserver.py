import doctest
import gzip
import os
import re
import shutil
import sys
import tempfile
from contextlib import closing

import mock
from zope.testing import renormalizing

from irclog2html.irclogserver import get_path, application


here = os.path.dirname(__file__)


def gzip_copy(src, dst):
    with open(src, 'rb') as fi:
        with closing(gzip.open(dst, 'wb')) as fo:
            shutil.copyfileobj(fi, fo)


def set_up_sample():
    tmpdir = tempfile.mkdtemp(prefix='irclog2html-test-')
    gzip_copy(os.path.join(here, 'sample.log'),
              os.path.join(tmpdir, 'sample-2013-03-17.log.gz'))
    shutil.copy(os.path.join(here, 'sample.log'),
                os.path.join(tmpdir, 'sample-2013-03-18.log'))
    with open(os.path.join(tmpdir, "index.html"), "w") as f:
        f.write("This is the index")
    with open(os.path.join(tmpdir, "font.css"), "w") as f:
        f.write("* { font: comic sans; }")
    return tmpdir


def clean_up_sample(tmpdir):
    shutil.rmtree(tmpdir)


def doctest_get_path():
    """Test for get_path.

    This function decides whether to search or to display a file based
    on URL path:

        >>> get_path(dict(PATH_INFO='/search'))
        'search'

        >>> get_path(dict(PATH_INFO='/#channel-2015-05-05.log.html'))
        '#channel-2015-05-05.log.html'

    When there is no file name, we show the index:

        >>> get_path(dict(PATH_INFO='/'))
        'index.html'

    Any slashes other than the leading one result in None:

        >>> get_path(dict(PATH_INFO='/../../etc/passwd'))

    """


def doctest_application():
    r"""Test for the WSGI entry point

        >>> tmpdir = set_up_sample()
        >>> start_response = mock.MagicMock()

        >>> environ = {
        ...     'IRCLOG_LOCATION': tmpdir,
        ...     'PATH_INFO': "/",
        ...     'wsgi.input': None,
        ... }

    When accessing the root, we get the index:

        >>> application(environ, start_response)
        [b'This is the index']
        >>> start_response.assert_called_once_with(
        ...     '200 Ok', [('Content-Type', 'text/html; charset=UTF-8')])

    We can load the stylesheet too, even if it's not copied to the log
    directory:

        >>> environ['PATH_INFO'] = '/irclog.css'
        >>> start_response = mock.MagicMock()
        >>> application(environ, start_response)
        [b'...div.searchbox {...']
        >>> start_response.assert_called_once_with(
        ...     '200 Ok', [('Content-Type', 'text/css')])

    We can load other CSS files, if needed

        >>> environ['PATH_INFO'] = '/font.css'
        >>> start_response = mock.MagicMock()
        >>> application(environ, start_response)
        [b'* { font: comic sans; }']
        >>> start_response.assert_called_once_with(
        ...     '200 Ok', [('Content-Type', 'text/css')])

    Accessing the search page:

        >>> environ['PATH_INFO'] = '/search'
        >>> start_response = mock.MagicMock()
        >>> application(environ, start_response)
        [b'<!DOCTYPE html PUBLIC...<title>Search IRC logs</title>...
        >>> start_response.assert_called_once_with(
        ...    '200 Ok', [('Content-Type', 'text/html; charset=UTF-8')])

    Searching the logs:

        >>> environ['PATH_INFO'] = '/search'
        >>> environ['QUERY_STRING'] = 'q=bot'
        >>> start_response = mock.MagicMock()
        >>> application(environ, start_response)
        [b'...<p>10 matches in 2 log files with 20 lines (... seconds).</p>...
        >>> start_response.assert_called_once_with(
        ...    '200 Ok', [('Content-Type', 'text/html; charset=UTF-8')])

    Retrieving log files:

        >>> environ['PATH_INFO'] = '/sample-2013-03-18.log'
        >>> del environ['QUERY_STRING']
        >>> start_response = mock.MagicMock()
        >>> application(environ, start_response)
        [b'2005-01-08T23:33:54 *** povbot has joined #pov...
        >>> start_response.assert_called_once_with(
        ...    '200 Ok', [('Content-Type', 'text/plain')])

    Accessing paths with slashes:

        >>> environ['PATH_INFO'] = '/./index.html'
        >>> start_response = mock.MagicMock()
        >>> application(environ, start_response)
        [b'Not found']
        >>> start_response.assert_called_once_with(
        ...    '404 Not Found', [('Content-Type', 'text/html; charset=UTF-8')])

    What if some poor soul runs Windows?

        >>> environ['PATH_INFO'] = '/.\\index.html'
        >>> start_response = mock.MagicMock()
        >>> application(environ, start_response)
        [b'Not found']
        >>> start_response.assert_called_once_with(
        ...    '404 Not Found', [('Content-Type', 'text/html; charset=UTF-8')])

    Accessing non-existing files:

        >>> environ['PATH_INFO'] = '/nonexistent'
        >>> start_response = mock.MagicMock()
        >>> application(environ, start_response)
        [b'Not found']
        >>> start_response.assert_called_once_with(
        ...    '404 Not Found', [('Content-Type', 'text/html; charset=UTF-8')])

    Clean up:

        >>> clean_up_sample(tmpdir)

    """


checker = None
if sys.version_info[0] == 2:
    checker = renormalizing.RENormalizing([
        (re.compile(r"^\['"), r"[b'"),
        (re.compile(r"u('.*?')"), r"\1"),
    ])


def test_suite():
    optionflags = (doctest.ELLIPSIS | doctest.REPORT_NDIFF |
                   doctest.NORMALIZE_WHITESPACE)
    return doctest.DocTestSuite(optionflags=optionflags, checker=checker)
