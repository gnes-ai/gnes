#  Tencent is pleased to support the open source community by making GNES available.
#
#  Copyright (C) 2019 THL A29 Limited, a Tencent company. All rights reserved.
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from os import path

from setuptools import setup, find_packages
from setuptools.extension import Extension

try:
    pkg_name = 'gnes'
    libinfo_py = path.join(pkg_name, '__init__.py')
    libinfo_content = open(libinfo_py, 'r', encoding='utf8').readlines()
    version_line = [l.strip() for l in libinfo_content if l.startswith('__version__')][0]
    exec(version_line)  # produce __version__
except FileNotFoundError:
    __version__ = '0.0.0'

try:
    with open('README.md', encoding='utf8') as fp:
        _long_description = fp.read()
except FileNotFoundError:
    _long_description = ''

extensions = [
    Extension(
        'gnes.indexer.chunk.bindexer.cython',
        ['gnes/indexer/chunk/bindexer/bindexer.pyx'],
        extra_compile_args=['-O3', '-g0'],
    ),
    Extension(
        'gnes.indexer.chunk.hbindexer.cython',
        ['gnes/indexer/chunk/hbindexer/hbindexer.pyx'],
        extra_compile_args=['-O3', '-g0'],
    ),
]

base_dep = [
    'numpy',
    'termcolor',
    'protobuf',
    'grpcio',
    'ruamel.yaml>=0.15.89',
    'pyzmq>=17.1.0']

# using pip install gnes[xx] is depreciated
# extras_dep is kept for legacy issue, will be removed soon

extras_dep = {
    'bert': ['bert-serving-server>=1.8.6', 'bert-serving-client>=1.8.6'],
    # 'elmo': [
    #     'elmoformanylangs @ git+https://github.com/HIT-SCIR/ELMoForManyLangs.git@master#egg=elmoformanylangs-0.0.2',
    #     'paramiko', 'pattern3'],
    'flair': ['flair>=0.4.1'],
    'annoy': ['annoy==1.15.2'],
    'chinese': ['jieba'],
    'vision': ['opencv-python>=4.0.0', 'imagehash>=4.0', 'image', 'peakutils'],
    'leveldb': ['plyvel>=1.0.5'],
    'test': ['pylint', 'memory_profiler>=0.55.0', 'psutil>=5.6.1', 'gputil>=1.4.0'],
    'transformers': ['pytorch-transformers'],
    'onnx': ['onnxruntime'],
    'audio': ['librosa>=0.7.0'],
    'scipy': ['scipy', 'sklearn'],
    'flask': ['flask'],
    'aiohttp': ['aiohttp'],
    'http': ['flask', 'aiohttp']
}


def combine_dep(new_key, base_keys):
    extras_dep[new_key] = list(set(k for v in base_keys for k in extras_dep[v]))


combine_dep('nlp', ['bert', 'flair', 'transformers'])
combine_dep('cn_nlp', ['chinese', 'nlp'])
combine_dep('all', [k for k in extras_dep if k != 'elmo'])

setup(
    name=pkg_name,
    packages=find_packages(),
    version=__version__,
    include_package_data=True,
    description='GNES is Generic Neural Elastic Search,'
                ' a cloud-native semantic search system based on deep neural network.',
    author='GNES team',
    author_email='team@gnes.ai',
    license='Apache 2.0',
    url='https://gnes.ai',
    download_url='https://github.com/gnes-ai/gnes/tags',
    long_description=_long_description,
    long_description_content_type='text/markdown',
    zip_safe=False,
    setup_requires=[
        'setuptools>=18.0',
        'cython',
    ],
    ext_modules=extensions,
    install_requires=base_dep,
    extras_require=extras_dep,
    entry_points={
        'console_scripts': ['gnes=gnes.cli:main'],
    },
    classifiers=(
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Cython',
        'Programming Language :: Unix Shell',
        'Environment :: Console',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Topic :: Database :: Database Engines/Servers',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
        'Topic :: Scientific/Engineering :: Image Recognition',
        'Topic :: Multimedia :: Video',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ),
    keywords='gnes cloud-native semantic search elastic neural-network encoding embedding serving',
)
