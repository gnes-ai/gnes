from os import path

from setuptools import setup, find_packages
from setuptools.extension import Extension

try:
    pkg_name = 'gnes'
    libinfo_py = path.join(pkg_name, '__init__.py')
    libinfo_content = open(libinfo_py, 'r').readlines()
    version_line = [l.strip() for l in libinfo_content if l.startswith('__version__')][0]
    exec(version_line)  # produce __version__
except FileNotFoundError:
    __version__ = '0.0.0'

try:
    with open('README.md') as fp:
        _long_description = fp.read()
except FileNotFoundError:
    _long_description = ''

extensions = [
    Extension(
        'gnes.indexer.bindexer.cython',
        ['gnes/indexer/bindexer/bindexer.pyx'],
        extra_compile_args=['-O3'],
    ),
    Extension(
        'gnes.indexer.hnsw_indexer.cython.hnsw',
        ['gnes/indexer/hnsw_indexer/cython/hnsw.pyx'],
        extra_compile_args=['-O3'],
    ),
    Extension(
        'gnes.indexer.hnsw_indexer.cython.heappq',
        ['gnes/indexer/hnsw_indexer/cython/heappq.pyx'],
        extra_compile_args=[
            '-O3'],
    ),
    Extension(
        'gnes.indexer.hnsw_indexer.cython.queue',
        ['gnes/indexer/hnsw_indexer/cython/queue.pyx'],
        extra_compile_args=[
            '-O3'],
    ),
    Extension(
        'gnes.indexer.hnsw_indexer.cython.prehash',
        ['gnes/indexer/hnsw_indexer/cython/prehash.pyx'],
        extra_compile_args=[
            '-O3'],
    ),
]

setup(
    name=pkg_name,
    packages=find_packages(),
    version=__version__,
    include_package_data=True,
    description='GNES is Generic Neural Elastic Search,'
                ' a highly scalable semantic search system based on deep neural network.',
    author='GNES team',
    author_email='artex.xh@gmail.com',
    license='Apache',
    url='https://github.com/tencent/gnes',
    long_description=_long_description,
    long_description_content_type='text/markdown',
    zip_safe=False,
    setup_requires=[
        'setuptools>=18.0',
        'cython',
    ],
    ext_modules=extensions,
    install_requires=[
        'numpy',
        'termcolor',
        'jieba',
        'protobuf',
        'bert-serving-server>=1.8.6',
        'bert-serving-client>=1.8.6',
        'plyvel>=1.0.5',
        'ruamel.yaml>=0.15.89',
        'psutil>=5.6.1',
        'memory_profiler>=0.55.0',
        'gputil>=1.4.0',
        'elmoformanylangs @ git+https://github.com/HIT-SCIR/ELMoForManyLangs.git@master#egg=elmoformanylangs-0.0.2',
        'flair>=0.4.1',
        'pytorch-pretrained-bert>=0.6.1',
        'pandas',
        'paramiko',
        'pattern3'
    ],
    extras_require={
        'test': ['pylint'],
    },
    entry_points={
        'console_scripts': ['gnes=gnes.cli:main'],
    },
    classifiers=(
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Cython',
        'Programming Language :: Unix Shell',
        'Environment :: Console',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Topic :: Database :: Database Engines/Servers'
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
        'Topic :: Scientific/Engineering :: Image Recognition',
        'Topic :: Multimedia :: Video'

    ),
    keywords='semantic search elastic neural-network encoding embedding serving',
)
