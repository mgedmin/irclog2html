#!/usr/bin/env python
import os
import re
from setuptools import setup


here = os.path.dirname(__file__)


def read(filename):
    with open(os.path.join(here, filename)) as f:
        return f.read()


long_description = read('README.rst') + '\n\n' + read('CHANGES.rst')

version_file = os.path.join(here, 'src/irclog2html/_version.py')
d = dict(re.findall('''(__version__) *= *'([^']*)''', read(version_file)))
version = d['__version__']

setup(
    name='irclog2html',
    version=version,
    author='Marius Gedminas',
    author_email='marius@gedmin.as',
    license='GPL v2 or later',
    platforms=['any'],
    url='http://mg.pov.lt/irclog2html/',
    description='Convert IRC logs to HTML',
    long_description=long_description,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    extras_require=dict(test=[
        "mock",
        "zope.testing",
    ]),
    packages=['irclog2html'],
    package_dir={'': 'src'},
    include_package_data=True,
    entry_points="""
        [console_scripts]
        irclog2html = irclog2html.irclog2html:main
        logs2html = irclog2html.logs2html:main
        irclogsearch = irclog2html.irclogsearch:main
        irclogserver = irclog2html.irclogserver:main
    """,
    zip_safe=False,
)
