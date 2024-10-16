"""
Search IRC logs (a CGI script and a WSGI app).

Expects to find logs matching the IRCLOG_GLOB pattern (default: *.log)
in the directory specified by the IRCLOG_LOCATION environment variable.
Expects the filenames to contain a ISO 8601 date (YYYY-MM-DD).

Apache configuration example:

  ScriptAlias /irclogs/search /path/to/irclogsearch.py
  <Location /irclogs/search>
    SetEnv IRCLOG_LOCATION /path/to/irclog/files/
    # Uncomment the following if your log files use a different format
    #SetEnv IRCLOG_GLOB "*.log.????-??-??"
  </Location>

"""

# Copyright (c) 2006-2013, Marius Gedminas and contributors
#
# Released under the terms of the GNU GPL v2 or v3
# https://www.gnu.org/copyleft/gpl.html

import cgi
import cgitb
import io
import os
import re
import sys
import time
from contextlib import closing
from urllib.parse import quote

from .irclog2html import (
    HOMEPAGE,
    RELEASE,
    VERSION,
    LogParser,
    NickColourizer,
    XHTMLTableStyle,
    escape,
    open_log_file,
)
from .logs2html import find_log_files


DEFAULT_LOGFILE_PATH = os.path.dirname(__file__)
DEFAULT_LOGFILE_PATTERN = "*.log"

DATE_REGEXP = re.compile(r'^.*(\d\d\d\d)-(\d\d)-(\d\d)')


HEADER = """\
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
          "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html>
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=%(charset)s" />
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>%(title)s</title>
  <link rel="stylesheet" href="irclog.css" />
  <meta name="generator" content="irclogsearch.py %(VERSION)s by Marius Gedminas" />
  <meta name="version" content="%(VERSION)s - %(RELEASE)s" />
</head>
<body>""" % {'VERSION': VERSION, 'RELEASE': RELEASE,
             'title': escape("Search IRC logs"), 'charset': 'UTF-8'}

FOOTER = """
<div class="generatedby">
<p>Generated by irclogsearch.py %(VERSION)s by <a href="mailto:marius@pov.lt">Marius Gedminas</a>
 - find it at <a href="%(HOMEPAGE)s">%(HOMEPAGE)s</a>!</p>
</div>
</body>
</html>""" % {'VERSION': VERSION,
              'HOMEPAGE': escape(HOMEPAGE)}


class Error(Exception):
    """Application error."""


class SearchStats(object):
    """Search statistics."""

    files = 0
    lines = 0
    matches = 0


class SearchResult(object):
    """Search result -- a single utterance."""

    def __init__(self, filename, link, date, time, event, info):
        self.filename = filename
        self.link = link
        self.date = date
        self.time = time
        self.event = event
        self.info = info


class SearchResultFormatter(object):
    """Formatter of search results."""

    def __init__(self, stream=None):
        self.stream = stream
        bstream = stream.buffer
        self.style = XHTMLTableStyle(bstream)
        self.nick_colour = NickColourizer()

    def print_prefix(self):
        print(self.style.prefix, file=self.stream)

    def print_html(self, result):
        link = urlescape(result.link)
        if result.event == LogParser.COMMENT:
            nick, text = result.info
            htmlcolour = self.nick_colour[nick]
            self.style.nicktext(result.time, nick, text, htmlcolour, link)
        else:
            if result.event == LogParser.NICKCHANGE:
                text, oldnick, newnick = result.info
                self.nick_colour.change(oldnick, newnick)
            else:
                text = result.info
            self.style.servermsg(result.time, result.event, text, link)

    def print_suffix(self):
        print(self.style.suffix, file=self.stream)


def urlescape(link):
    return escape(quote(link))


def parse_log_file(filename):
    with closing(open_log_file(filename)) as f:
        for row in LogParser(f):
            yield row


def search_irc_logs(query, stats=None, where=DEFAULT_LOGFILE_PATH,
                    logfile_pattern=DEFAULT_LOGFILE_PATTERN, limit=None):
    if not stats:
        stats = SearchStats() # will be discarded, but, oh, well
    query = query.lower()
    files = find_log_files(where, logfile_pattern)
    files.reverse() # newest first
    for f in files:
        date = f.date
        link = f.link
        stats.files += 1
        for timestamp, event, info in parse_log_file(f.filename):
            if event == LogParser.COMMENT:
                nick, text = info
                text = nick + ' ' + text
            elif event == LogParser.NICKCHANGE:
                text, oldnick, newnick = info
            else:
                text = str(info)
            stats.lines += 1
            if query in text.lower():
                stats.matches += 1
                yield SearchResult(f.filename, link, date, timestamp, event, info)
                if stats.matches == limit:
                    return


def print_cgi_headers(stream):
    print("Content-Type: text/html; charset=UTF-8", file=stream)
    print("", file=stream)


def print_search_form(stream=None):
    if stream is None:
        stream = sys.stdout
    print(HEADER, file=stream)
    print("<h1>Search IRC logs</h1>", file=stream)
    print('<form action="" method="get">', file=stream)
    print('<input type="text" name="q" />', file=stream)
    print('<input type="submit" />', file=stream)
    print('</form>', file=stream)
    print(FOOTER, file=stream)


def print_search_results(query, where=DEFAULT_LOGFILE_PATH,
                         logfile_pattern=DEFAULT_LOGFILE_PATTERN,
                         limit=100,
                         stream=None):
    if stream is None:
        stream = sys.stdout
    print(HEADER, file=stream)
    print("<h1>IRC log search results for %s</h1>" % escape(query), file=stream)
    print('<form action="" method="get">', file=stream)
    print('<input type="text" name="q" value="%s" />' % escape(query),
          file=stream)
    print('<input type="submit" />', file=stream)
    print('</form>', file=stream)
    started = time.time()
    date = None
    prev_result = None
    formatter = SearchResultFormatter(stream)
    stats = SearchStats()
    for result in search_irc_logs(query, stats=stats, where=where,
                                  logfile_pattern=logfile_pattern,
                                  limit=limit):
        if date != result.date:
            if prev_result:
                formatter.print_suffix()
                prev_result = None
            if date:
                print("  </li>", file=stream)
            else:
                print('<ul class="searchresults">', file=stream)
            print('  <li><a href="%s">%s</a>:' %
                  (urlescape(result.link),
                   result.date.strftime('%Y-%m-%d (%A)')),
                  file=stream)
            date = result.date
        if not prev_result:
            formatter.print_prefix()
        formatter.print_html(result)
        prev_result = result
    if prev_result:
        formatter.print_suffix()
    if date:
        print("  </li>", file=stream)
        print("</ul>", file=stream)
    total_time = time.time() - started
    print("<p>%d matches in %d log files with %d lines (%.1f seconds).</p>"
          % (stats.matches, stats.files, stats.lines, total_time),
          file=stream)
    print(FOOTER, file=stream)


def unicode_stdout():
    stream = sys.stdout.buffer
    return io.TextIOWrapper(stream, 'ascii',
                            errors='xmlcharrefreplace',
                            line_buffering=True)


def search_page(stream, form, where, logfile_pattern):
    if "q" not in form:
        print_search_form(stream)
    else:
        search_text = form["q"].value
        print_search_results(search_text, stream=stream, where=where,
                             logfile_pattern=logfile_pattern)


def main():
    """CGI script"""
    cgitb.enable()
    logfile_path = os.getenv('IRCLOG_LOCATION') or DEFAULT_LOGFILE_PATH
    logfile_pattern = os.getenv('IRCLOG_GLOB') or DEFAULT_LOGFILE_PATTERN
    form = cgi.FieldStorage()
    stream = unicode_stdout()
    print_cgi_headers(stream)
    search_page(stream, form, logfile_path, logfile_pattern)


if __name__ == '__main__':
    main()
