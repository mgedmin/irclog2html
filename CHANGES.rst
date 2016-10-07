Changelog
=========

2.15.2 (2016-10-07)
-------------------

- ``irclogserver`` channel list is now split into old channels and active
  channels, detected by checking whether the directory modification date
  is newer or older than 7 days.

- 2nd-level headings now have the same color as 1st-level headings.

- ``irclogserver`` no longer shows a 404 if you omit the trailing ``/``
  after a channel name in the URL.


2.15.1 (2016-09-25)
-------------------

- Lines with the same timestamp now get different HTML anchors
  (https://github.com/mgedmin/irclog2html/issues/17).  Thanks
  to Bryan Bishop for the original pull request.


2.15.0 (2016-09-25)
-------------------

- There's a new ``irclogserver`` script that can be used to serve
  dynamically-generated IRC logs and perform search.  It can also be
  deployed via WSGI.  Portions contributed by Albertas Agejevas
  (https://github.com/mgedmin/irclog2html/pull/9).

- Index pages group the logs by month
  (https://github.com/mgedmin/irclog2html/issues/12).

- Drop support for Python 2.6.


2.14.0 (2014-12-12)
-------------------

- Add -o option to specify the output file name.  Patch by Moises Silva
  (https://github.com/mgedmin/irclog2html/pull/7).


2.13.1 (2014-02-01)
-------------------

- Add support for Windows (e.g. refrain from creating latest.log.html
  symlinks).


2.13.0 (2013-12-18)
-------------------

- Handle gzipped files transparently
  (https://github.com/mgedmin/irclog2html/issues/5).


2.12.1 (2013-03-22)
-------------------

* Fix AttributeError in irclogsearch on Python 2.7
  (https://github.com/mgedmin/irclog2html/issues/1).


2.12.0 (2013-03-18)
-------------------

* Moved to Github.

* Add support for Python 3.3.

* Drop support for Python 2.4 and 2.5.

* Fix URL linkifier to not include trailing punctuation (LP#1155906).


2.11.1 (2013-03-17)
-------------------

* logs2html also accepts filenames that contain YYYYMMDD dates (in addition to
  YYYY-MM-DD).  Patch by Holger Just.  Fixes LP#1031642.


2.11.0 (2012-07-30)
-------------------

* irclogsearch can be told about the filename pattern of log files via an
  environment variable (IRCLOG_GLOB).  Patch by Jonathan Kinred.


2.10.0 (2012-02-12)
-------------------

* New option: --glob-pattern.  Patch by Albertas Agejevas.
  Fixes LP#912310.

* Links in logs are marked with rel="nofollow".  Patch by Matt Wheeler.
  Fixes LP#914553.

* New option: --version.

* New option: -c, --config=FILE.


2.9.2 (2011-01-16)
------------------

* Support XChat Latin/Unicode hybrid encoding (http://xchat.org/encoding/).
  Fixes LP#703622.

* irclog2html copies irclog.css file into the destination directory.
  Fixes LP#608727.


2.9.1 (2010-08-06)
------------------

* Make sure irclog.css is installed in the right place; logs2html needs it.


2.9 (2010-08-06)
----------------

* Restructured source tree, made irclogs2html into a package, added setup.py,
  buildout.cfg, bootstrap.py, Makefile, HACKING.txt; moved old porting test
  suite into a subdirectory (porting).

* logs2html copies irclog.css file into the destination directory.

* Released into PyPI.


2.8 (2010-07-22)
----------------

* Added README.txt and CHANGES.txt.

* Support dircproxy log files (new date format: "[15 Jan 08:42]",
  strip ident and IP address from nicknames).  Patch by Paul Frields.

* New option: --dircproxy also makes irclog2html strip a single leading
  '+' or '-' from messages.


2.7.1 (2009-04-30)
------------------

* Bug in logs2html.py error reporting, reported by Ondrej Baudys.


2.7 (2008-06-10)
----------------

* New style: mediawiki.  Patch by Ian Weller.


2.6 (2007-10-30)
----------------

* Support another date format (Oct 17 10:53:26).  Patch by Matthew Barnes.


2.5.1 (2007-03-22)
------------------

* logs2html.py: add a stable link to the latest log file
  (suggested by Chris Foster).


2.5 (2007-01-22)
----------------

* New option: --searchbox.

* Search CGI script improvements (e.g. put newest matches on top).


2.4 (2006-12-11)
----------------

* Added a sample CGI script for brute-force log searches.


2.3 (2005-03-08)
----------------

* Use xhtmltable style by default.

* Added a copy of the navbar at the bottom.


2.2 (2005-02-04)
----------------

* Support supybot's ChannelLogger date format (e.g. 02-Feb-2004).

* Fixed broken timestamp hyperlinks in xhtml/xhtmltable styles.

* CSS tweaks.


2.1mg (2005-01-09)
------------------

* Ported irclog2html.pl version 2.1 by Jeff Waugh from Perl to Python.

* New styles: xhtml, xhtmltable.

* New options: --title, --{prev,index,next}-{url,title}

* Removed hardcoded nick colour preferences for jdub, cantaker and chuckd

* Bugfix: colours are preserver accross nick changes (irclog2html.pl tried to
  do that, but had a bug in a regex)

* Added ISO8601 timestamp support (e.g. 2005-01-09T12:43:11).

* More careful URL linkification (stop at ', ", ), >).

* Added logs2html.py script for mass-conversion of logs.

* Added support for xchat log files.

* Added xchatlogsplit.py script for splitting xchat logs on day boundaries so they're suitable as input for logs2html.py.
