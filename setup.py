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


import distutils.core as mod_distutilscore

mod_distutilscore.setup(
    name='trackanimation',
    version='1.0.0',
    description='GPS Track Animation Library',
    license='Apache License, Version 2.0',
    author='Juan José Martín',
    author_email='',
    url='https://github.com/JoanMartin/trackanimation',
    packages=['trackanimation', ],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
    ],
    scripts=['']
)