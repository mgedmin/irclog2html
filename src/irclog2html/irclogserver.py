#!/usr/bin/env python
"""
Serve IRC logs (WSGI app)

Expects to find logs matching the IRCLOG_GLOB pattern (default: *.log)
in the directory specified by the IRCLOG_LOCATION environment variable.
Expects the filenames to contain a ISO 8601 date (YYYY-MM-DD).

Apache configuration example:

  WSGIScriptAlias /irclogs /path/to/irclogserver.py
  <Location /irclogs>
    SetEnv IRCLOG_LOCATION /path/to/irclog/files/
    # Uncomment the following if your log files use a different format
    #SetEnv IRCLOG_GLOB "*.log.????-??-??"
  </Location>

"""

# Copyright (c) 2015, Marius Gedminas and contributors
#
# Released under the terms of the GNU GPL
# http://www.gnu.org/copyleft/gpl.html

from __future__ import print_function

import cgi
import io
import os

try:
    from urllib import quote_plus # Py2
except ImportError:
    from urllib.parse import quote_plus # Py3

from .irclog2html import CSS_FILE, LogParser
from .irclogsearch import (
    DEFAULT_LOGFILE_PATH, DEFAULT_LOGFILE_PATTERN, search_page,
    HEADER, FOOTER
)


def dir_listing(stream, path):
    """Primitive listing of subdirectories"""
    print(HEADER, file=stream)
    print(u"<h1>IRC logs</h1>", file=stream)
    print(u"<ul>", file=stream)
    for name in sorted(os.listdir(path)):
        if os.path.isdir(os.path.join(path, name)):
            print(u'<li><a href="%s/">%s</a></li>'
                  % (quote_plus(name), cgi.escape(name)),
                  file=stream)
    print(u"</ul>", file=stream)
    print(FOOTER, file=stream)


def parse_path(environ):
    """Return tuples (channel, filename).

    The channel of None means default, the filename of None means 404.
    """
    path = environ.get('PATH_INFO', '/')
    path = path[1:]  # Remove the leading slash
    channel = None
    if environ.get('IRCLOG_CHAN_DIR'):
        if '/' in path:
            channel, path = path.split('/', 1)
            if channel == '..':
                return None, None
    if '/' in path or '\\' in path:
        return channel, None
    return channel, path if path != '' else 'index.html'


def application(environ, start_response):
    """WSGI application"""
    def getenv(name, default=None):
        return environ.get(name, os.environ.get(name, default))

    chan_path = getenv('IRCLOG_CHAN_DIR')
    logfile_path = getenv('IRCLOG_LOCATION') or DEFAULT_LOGFILE_PATH
    logfile_pattern = getenv('IRCLOG_GLOB') or DEFAULT_LOGFILE_PATTERN
    form = cgi.FieldStorage(fp=environ['wsgi.input'], environ=environ)
    stream = io.TextIOWrapper(io.BytesIO(), 'ascii',
                              errors='xmlcharrefreplace',
                              line_buffering=True)

    status = "200 Ok"
    content_type = "text/html; charset=UTF-8"
    headers = {}

    channel, path = parse_path(environ)
    if channel:
        logfile_path = os.path.join(chan_path, channel)
    if path is None:
        status = "404 Not Found"
        result = [b"Not found"]
        content_type = "text/plain"
    elif path == "index.html" and chan_path and channel is None:
        dir_listing(stream, chan_path)
        result = [stream.buffer.getvalue()]
    elif path == 'search':
        fmt = search_page(stream, form, logfile_path, logfile_pattern)
        result = [stream.buffer.getvalue()]
        del fmt
    elif path == 'irclog.css':
        content_type = "text/css"
        try:
            with open(CSS_FILE, "rb") as f:
                result = [f.read()]
        except IOError:  # pragma: nocover
            status = "404 Not Found"
            result = [b"Not found"]
            content_type = "text/plain"
    else:
        try:
            with open(os.path.join(logfile_path, path), "rb") as f:
                result = [f.read()]
        except IOError:
            if path == 'index.html':
                # no index? redirect to search page
                status = "302 Found"
                result = [b"Try /search"]
                headers['Location'] = '/search'
                content_type = "text/plain"
            else:
                status = "404 Not Found"
                result = [b"Not found"]
                content_type = "text/plain"
        else:
            if path.endswith('.css'):
                content_type = "text/css"
            elif path.endswith('.log') or path.endswith('.txt'):
                content_type = "text/plain; charset=UTF-8"
                result = [LogParser.decode(line).encode('UTF-8')
                          for line in b''.join(result).splitlines(True)]

    headers["Content-Type"] = content_type
    # We need str() for Python 2 because of unicode_literals
    headers = sorted((str(k), str(v)) for k, v in headers.items())
    start_response(str(status), headers)
    return result


def main():  # pragma: nocover
    """Simple web server for manual testing"""
    from wsgiref.simple_server import make_server
    srv = make_server('localhost', 8080, application)
    print("Started at http://localhost:8080/")
    srv.serve_forever()


if __name__ == '__main__':
    main()
