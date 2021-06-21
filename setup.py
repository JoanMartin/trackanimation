# -*- coding: utf-8 -*-

# Copyright 2017 Juan José Martín Miralles
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from os import path
from codecs import open
from setuptools import setup

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='trackanimation',

    version='1.0.5',

    description='GPS Track Animation Library',
    long_description=long_description,

    url='https://github.com/JoanMartin/trackanimation',

    author='Juan José Martín',
    author_email='',

    license='Apache License, Version 2.0',

    classifiers=[
        "Development Status :: 5 - Production/Stable",

        "License :: OSI Approved :: Apache Software License",

        "Intended Audience :: Education",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Science/Research",

        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Multimedia :: Video",

        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
    ],

    keywords='GPS GPX animation map geospatial geopositioning',

    packages=['trackanimation', ],

    install_requires=[
        'geopy>=1.16.0',
        'gpxpy>=1.3.3',
        'pillow>=5.2.0',
        'matplotlib>=2.2.3',
        'mplleaflet==0.0.5',
        'pandas>=0.23.4',
        'tqdm>=4.25.0',
        'smopy==0.0.7',
    ],
)
