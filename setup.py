#!/usr/bin/env python

import os
import io
import sys

from setuptools import setup
__version__ = "0.3.3"

with io.open('README.md', 'r', encoding='utf-8') as readme_file:
    readme = readme_file.read()

with io.open('CHANGELOG.md', 'r', encoding='utf-8') as history_file:
    history = history_file.read()

requirements = [
    'pygithub-redux>=1.29.0',
    'click',
    'jinja2',
    'tqdm',
]

long_description = readme + '\n\n' + history

setup(
    name='statuspage',
    version=__version__,
    description=('A statuspage generator that lets you host your statuspage for free on Github.'),
    long_description=long_description,
    author='Jannis Gebauer',
    author_email='ja.geb@me.com',
    url='https://github.com/jayfk/statuspage',
    entry_points='''
        [console_scripts]
        statuspage=statuspage.statuspage:cli
    ''',
    packages=['statuspage'],
    package_data={'': ["template/*"]},
    include_package_data=True,
    install_requires=requirements,
    license='MIT',
    zip_safe=False,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development',
    ],
    keywords="statuspage"
)
