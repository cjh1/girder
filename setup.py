#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#  Copyright 2013 Kitware Inc.
#
#  Licensed under the Apache License, Version 2.0 ( the "License" );
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
###############################################################################

from setuptools import setup, find_packages
from pip.req import parse_requirements
import sys
import os

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

# parse_requirements() returns generator of pip.req.InstallRequirement objects
install_reqs = parse_requirements('requirements.txt')

# reqs is a list of requirement
reqs = [str(ir.req) for ir in install_reqs]

setup(
    name='girder',
    version='0.1.22',
    description='High-performance data management.',
    long_description=readme,
    author='Kitware',
    author_email='kitware@kitware.com',
    url='https://github.com/girder/girder',
    packages=find_packages(exclude=('tests', 'docs')),
    license='Apache 2.0',
    zip_safe=True,
    install_requires=reqs,
    package_dir={'girder': 'girder'},
    package_data={'girder': ['conf/girder.dist.cfg',
                             '../clients/web/lib/js/*',
                             '../clients/web/static/built/*.js',
                             '../clients/web/static/built/*.css',
                             '../clients/web/static/built/*.html',
                             '../clients/web/static/built/swagger/*.js',
                             '../clients/web/static/built/swagger/*.css',
                             '../clients/web/static/built/swagger/*.html',
                             '../clients/web/static/built/swagger/css/*',
                             '../clients/web/static/built/swagger/images/*',
                             '../clients/web/static/built/swagger/lib/*.js',
                             '../clients/web/static/built/swagger/lib/shred/*.js',
                             '../clients/web/static/img/*',
                             '../clients/web/static/lib/bootstrap/css/*',
                             '../clients/web/static/lib/fontello/css/*',
                             '../clients/web/static/lib/fontello/font/*',
                             '../clients/web/static/lib/jqplot/css/*']},
    classifiers=(
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
    )
)
