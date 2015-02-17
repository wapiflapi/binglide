#!/usr/bin/env python

import sys

if sys.version_info < (3, 3, 0):
    sys.stdout.write("It's %d. This requires Python > 3.3.\n" % datetime.now().year)
    sys.exit(1)

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import binglide

readme = open('README.md').read()
requirements = open('requirements.txt').read()

setup(
    name='binglide',
    version=binglide.__version__,
    description='Tool for visual data analysis.',
    long_description=readme,
    author=binglide.__author__,
    author_email=binglide.__email__,
    url='https://github.com/wapiflapi/binglide',
    license="MIT",
    zip_safe=False,
    keywords='binglide',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],

    scripts=['bin/binglide', 'bin/binglide-server'],
    packages=['binglide', 'binglide.server', 'binglide.server.workers'],
    package_dir={'binglide': 'binglide'},
    package_data={'': ['*.yaml']},
    install_requires=requirements,
)
