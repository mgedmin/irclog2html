#!/usr/bin/env python
import os
from setuptools import setup


here = os.path.dirname(__file__)


def read(filename):
    return open(os.path.join(here, filename)).read()


long_description = read('README.txt') + '\n\n' + read('CHANGES.txt')

version_file = os.path.join(here, 'src/irclog2html/_version.py')
d = {}
execfile(version_file, d)
version = d['__version__']

setup(
    name='irclog2html',
    version=version,
    author='Marius Gedminas',
    author_email='marius@gedmin.as',
    license='GPL',
    platforms=['any'],
    url='http://mg.pov.lt/irclog2html/',
    description='Convert IRC logs to HTML',
    long_description=long_description,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.4',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
    packages=['irclog2html'],
    package_dir={'': 'src'},
    include_package_data=True,
    entry_points="""
        [console_scripts]
        irclog2html = irclog2html.irclog2html:main
        logs2html = irclog2html.logs2html:main
        irclogsearch = irclog2html.irclogsearch:main
    """,
    zip_safe=False,
)
