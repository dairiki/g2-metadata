# -*- coding: utf-8 -*-
import os
import sys

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

VERSION = '0.1b1'

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()

requires = [
    'sqlalchemy',
    'MySQL-python',
    'phpserialize',
    'PyYAML',
    'bbcode',
    'html2text',
    'jinja2',
    'piexif',
    'click',
    'six',
    ]

testing_extras = [
    'pytest',
    ]

tests_require = testing_extras[:]


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)

cmdclass = {'test': PyTest}

setup(
    name='g2-metadata',
    version=VERSION,
    description='Dump gallery2 metadata to YAML',
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python",
        "Environment :: Console",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: BSD License",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Utilities",
        ],
    author='Jeff Dairiki',
    author_email='dairiki@dairiki.org',
    url='',
    keywords='gallery2',

    packages=find_packages(),

    install_requires=requires,

    include_package_data=True,
    zip_safe=True,

    entry_points={
        'console_scripts': [
            'g2-metadata = g2_metadata.main:main',
            'g2-yaml-to-pck = g2_metadata.loader:yaml_to_pck',
            ],
        },

    tests_require=tests_require,
    cmdclass=cmdclass,
    extras_require={
        "testing": testing_extras,
        },
    )
