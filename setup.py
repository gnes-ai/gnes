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
    description='Generic Neural Elastic Search is an end-to-end solution for semantic text search.',
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
        'bert-serving-server',
        'bert-serving-client',
        'plyvel',
        'joblib',
        'ruamel.yaml',
        'psutil',
        'memory_profiler',
        'gputil'
    ],
    extras_require={
        'test': ['pylint'],
    },
)
