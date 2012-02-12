===========
irclog2html
===========

Converts IRC log files to HTML with pretty colours.


Quick start
===========

Installation::

  pip install irclog2html

Quick usage for a single log file::

  irclog2html --help
  irclog2html filename.log                  (produces filename.log.html)

Mass-conversion of logs (one file per day, with YYYY-MM-DD in the filename)
with next/prev links, with mtime checks, usable from cron::

  logs2html directory/            (looks for *.log, produces *.log.html)


Configuration files
===================

Since you probably don't want to keep specifying the same options on the
command line every time you run logs2html, you can create a config file.
For example::

  -t 'IRC logs for #mychannel'
  -p 'IRC logs for #mychannel for '
  # the following needs some extra Apache setup to enable the CGI script
  --searchbox
  # where we keep the logs
  /full/path/to/directory/

Use it like this::

  logs2html -c /path/to/mychannel.conf

Lines starting with a ``#`` are ignored.  Other lines are interpreted as 
command-line options.

The order matters: options on the command line before the ``-c FILE`` will
be overriden by option in the config file.  Options specified after ``-c FILE``
will override the options in the config file.

You can include more than one config file by repeating ``-c FILE``.  You
can include config files from other config files.  You can even create loops of
config files and then watch and laugh manically as logs2html sits there burning
your CPU.


CGI script for log searching
============================

.. warning::
   The script can be easily abused to cause a denial of service attack; it
   parses *all* log files every time you perform a search.

You can generate search boxes on IRC log pages by passing the ``--searchbox``
option to ``logs2html``.  Here's an example Apache config snippet that makes
it work::

  RewriteRule ^/my-irclog/search/$ /my-irclog/search [R,L]
  ScriptAlias /my-irclog/search /usr/local/bin/irclogsearch
  <Location /my-irclog/search>
    SetEnv IRCLOG_LOCATION "/var/www/my-irclog/"
  </Location>


Misc
====

Website: http://mg.pov.lt/irclog2html/

Bug tracker: https://bugs.launchpad.net/irclog2html

Licence: GPL v2 or later (http://www.gnu.org/copyleft/gpl.html)
