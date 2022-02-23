#!/usr/bin/env python

import os
import io
import sys

from setuptools import setup
__version__ = "1.0"

with io.open('README.md', 'r', encoding='utf-8') as readme_file:
    readme = readme_file.read()

with io.open('CHANGELOG.md', 'r', encoding='utf-8') as history_file:
    history = history_file.read()

requirements = [
    'pygithub',
    'click',
    'jinja2',
    'tqdm',
    'requests',
    'markdown2'
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
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        "Programming Language :: Python :: 3",
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development',
    ],
    keywords="statuspage"
)
