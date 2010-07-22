irclog2html
===========

Converts IRC log files to HTML with pretty colours.

Quick usage for a single log file::

  irclog2html.py --help
  irclog2html.py filename.log                  (produces filename.log.html)

Mass-conversion of logs (one file per day, with YYYY-MM-DD in the filename)
with next/prev links, with mtime checks, usable from cron::

  logs2html.py directory/            (looks for *.log, produces *.log.html)

You'll probably also want to copy irclog.css to the directory with HTML files,
as irclog2html doesn't do that yet.


Website: http://mg.pov.lt/irclog2html/

Bug tracker: https://bugs.launchpad.net/irclog2html

Licence: GPL v2 or later (http://www.gnu.org/copyleft/gpl.html)
