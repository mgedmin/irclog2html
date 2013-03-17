Developing irclog2html
======================

To play with the scripts without installing, use::

    make
    bin/irclog2html --help
    bin/logs2html --help

To run the test suite, use::

    make test

The testcases directory contains some sample logs, so you can try ::

    bin/logs2html testcases

and look at testcases/index.html afterwards.

To play with the CGI script, try ::

    IRCLOG_LOCATION=testcases bin/irclogsearch q=query


But I don't have make!
======================

Don't worry, feel free to use buildout directly::

    python bootstrap.py
    bin/buildout
    bin/test
    bin/irclog2html --help
    bin/logs2html --help

