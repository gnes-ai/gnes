from os import path

from setuptools import setup, find_packages
from setuptools.extension import Extension

pkg_name = 'gnes'
libinfo_py = path.join(pkg_name, '__init__.py')
libinfo_content = open(libinfo_py, 'r').readlines()
version_line = [l.strip() for l in libinfo_content if l.startswith('__version__')][0]
exec(version_line)  # produce __version__

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
    package_data={pkg_name: ['resources']},
    description='Generic Neural Elastic Search is an end-to-end solution for semantic text search',
    author='GNES team',
    url='https://github.com',
    long_description=open('README.md').read(),
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
        'bert-serving-server>=1.8.6',
        'bert-serving-client>=1.8.6',
        'plyvel>=1.0.5',
        'joblib>=0.13.2',
        'ruamel.yaml>=0.15.89',
        'psutil>=5.6.1',
        'memory_profiler>=0.55.0',
        'gputil>=1.4.0',
        'elmoformanylangs @ git+https://github.com/HIT-SCIR/ELMoForManyLangs.git@master#egg=elmoformanylangs-0.0.2'
    ],
    extras_require={
        'test': ['pylint'],
    },
    entry_points={
        'console_scripts': ['gnes=gnes.cli:main'],
    },
)
