import doctest


# Just test that there are no syntax errors and main() can imported; there's
# no actual code in __main__.py.


def doctest_main_can_be_imported():
    """Test for __main__.py

        >>> from irclog2html.__main__ import main  # noqa

    """


def test_suite():
    optionflags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS | doctest.REPORT_NDIFF
    return doctest.DocTestSuite(optionflags=optionflags)
