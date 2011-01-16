#!/usr/bin/env python
import os
from setuptools import setup


def read(filename):
    here = os.path.dirname(__file__)
    return open(os.path.join(here, filename)).read()


long_description = read('README.txt') + '\n\n' + read('CHANGES.txt')

setup(
    name='irclog2html',
    version='2.9.3dev',
    author='Marius Gedminas',
    author_email='marius@gedmin.as',
    license='GPL',
    platforms=['any'],
    url='http://mg.pov.lt/irclog2html/',
    description='Convert IRC logs to HTML',
    long_description=long_description,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
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
    zip_safe = False,
)
