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

  logs2html directory/     (looks for *.log and *.log.gz, produces *.log.html)


Configuration files
===================

Since you probably don't want to keep specifying the same options on the
command line every time you run logs2html, you can create a config file.
For example::

  -t 'IRC logs for #mychannel'
  -p 'IRC logs for #mychannel for '
  # the following needs some extra Apache setup to enable the CGI/WSGI script
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
    # Uncomment the following if your log files use a different format
    #SetEnv IRCLOG_GLOB "*.log.????-??-??"
    # (this will also automatically handle *.log.????-??-??.gz)
  </Location>


WSGI script for log serving
===========================

.. warning::
   The script can be easily abused to cause a denial of service attack; it
   parses *all* log files every time you perform a search.

There's now an experimental WSGI script that can generate HTML for the
logs on the fly.  You can use it if you don't like cron scripts and CGI.

Here's an example Apache config snippet::

  WSGIScriptAlias /irclogs /usr/local/bin/irclogserver
  <Location /irclogs>
    SetEnv IRCLOG_LOCATION "/var/www/my-irclog/"
    # Uncomment the following if your log files use a different format
    #SetEnv IRCLOG_GLOB "*.log.????-??-??"
    # (this will also automatically handle *.log.????-??-??.gz)
  </Location>

Currently it has certain downsides:

- configuration is very limited, e.g you cannot specify titles or styles
  or enable dircproxy mode
- HTML files in the irc log directory will take precedence over
  dynamically-generated logs even if they're older than the corresponding
  log file (but on the plus side you can use that to have dynamic search
  via WSGI, but keep statically-generated HTML files with your own config
  tweaks)


WSGI script for multi-channel log serving
=========================================

.. warning::
   The script can be easily abused to cause a denial of service attack; it
   parses *all* log files every time you perform a search.

The experimental WSGI script can serve logs for multiple channels::

  WSGIScriptAlias /irclogs /usr/local/bin/irclogserver
  <Location /irclogs>
    SetEnv IRCLOG_CHAN_DIR "/var/www/my-irclog/"
    # Uncomment the following if your log files use a different format
    #SetEnv IRCLOG_GLOB "*.log.????-??-??"
    # (this will also automatically handle *.log.????-??-??.gz)
  </Location>

Now ``/irclogs`` will show a list of channels (subdirectories under
``/var/www/my-irclog/``), and ``/irclogs/channel/`` will show the
date index for that channel.


Misc
====

Website: https://mg.pov.lt/irclog2html/

Bug tracker:
https://github.com/mgedmin/irclog2html/issues

Licence: GPL v2 or v3 (https://www.gnu.org/copyleft/gpl.html)

|buildstatus|_ |appveyor|_ |coverage|_

.. |buildstatus| image:: https://github.com/mgedmin/irclog2html/workflows/build/badge.svg?branch=master
.. _buildstatus: https://github.com/mgedmin/irclog2html/actions

.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/github/mgedmin/irclog2html?branch=master&svg=true
.. _appveyor: https://ci.appveyor.com/project/mgedmin/irclog2html

.. |coverage| image:: https://coveralls.io/repos/mgedmin/irclog2html/badge.svg?branch=master
.. _coverage: https://coveralls.io/r/mgedmin/irclog2html

