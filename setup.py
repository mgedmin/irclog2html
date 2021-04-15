#!/usr/bin/env python
import os
import re
from io import open

from setuptools import setup


here = os.path.dirname(__file__)


def read(filename):
    with open(os.path.join(here, filename), encoding='utf-8') as f:
        return f.read()


long_description = read('README.rst') + '\n\n' + read('CHANGES.rst')

version_file = os.path.join(here, 'src/irclog2html/_version.py')
d = dict(re.findall('''(__[a-z]+__) *= *'([^']*)''', read(version_file)))
version = d['__version__']
homepage = d['__homepage__']

setup(
    name='irclog2html',
    version=version,
    author='Marius Gedminas',
    author_email='marius@gedmin.as',
    license='GPL v2 or v3',
    platforms=['any'],
    url=homepage,
    description='Convert IRC logs to HTML',
    long_description=long_description,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    keywords='irc log colorizer html wsgi',
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
