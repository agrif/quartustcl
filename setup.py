#!/usr/bin/env python3
from os import path

from setuptools import find_packages, setup

# read our README
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='quartustcl',
    url='https://github.com/agrif/quartustcl/',
    description='a Python package for interfacing with Intel Quartus Tcl',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Aaron Griffith',
    author_email='aargri@gmail.com',
    license='MIT',
    platforms=['any'],

    project_urls={
        'Source': 'https://github.com/agrif/quartustcl/',
        'Documentation': 'https://quartustcl.readthedocs.io/en/latest/',
    },

    keywords='quartus tcl',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',

        'Topic :: Scientific/Engineering :: '
        'Electronic Design Automation (EDA)',

        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],

    setup_requires=[
        'setuptools_git >= 0.3',
        'better-setuptools-git-version >= 1.0',
    ],
    extras_require={
        'docs': ['mkdocs >= 1.0', 'mkautodoc >= 0.1.0'],
    },
    version_config={
        'version_format': '{tag}.dev{sha}',
    },

    packages=find_packages(exclude=['tests', 'tests.*']),
    python_requires='>=3.5',
    test_suite='tests',
)
