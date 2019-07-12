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
        'gnes.indexer.vector.bindexer.cython',
        ['gnes/indexer/vector/bindexer/bindexer.pyx'],
        extra_compile_args=['-O3'],
    ),
    Extension(
        'gnes.indexer.vector.hbindexer.cython',
        ['gnes/indexer/vector/hbindexer/hbindexer.pyx'],
        extra_compile_args=['-O3'],
    ),
]

base_dep = [
    'numpy',
    'scipy',
    'termcolor',
    'protobuf',
    'grpcio',
    'ruamel.yaml>=0.15.89',
    'aiohttp==3.5.4',
    'pyzmq>=17.1.0',
]
bert_dep = ['bert-serving-server>=1.8.6', 'bert-serving-client>=1.8.6']
elmo_dep = ['elmoformanylangs @ git+https://github.com/HIT-SCIR/ELMoForManyLangs.git@master#egg=elmoformanylangs-0.0.2',
            'paramiko', 'pattern3']
flair_dep = ['flair>=0.4.1']
nlp_dep = list(set(bert_dep + flair_dep))
annoy_dep = ['annoy==1.15.2']
chinese_dep = ['jieba']
cn_nlp_dep = list(set(chinese_dep + nlp_dep))
vision_dep = ['opencv-python>=4.0.0', 'torchvision==0.3.0', 'imagehash>=4.0']
leveldb_dep = ['plyvel>=1.0.5']
test_dep = ['pylint', 'memory_profiler>=0.55.0', 'psutil>=5.6.1', 'gputil>=1.4.0']
all_dep = list(set(base_dep + cn_nlp_dep + vision_dep + leveldb_dep + test_dep + annoy_dep))

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
    extras_require={
        'bert': bert_dep,
        # 'elmo': elmo_dep,   # not welcome by pip
        'flair': flair_dep,
        'nlp': nlp_dep,
        'annoy': annoy_dep,
        'chinese': chinese_dep,
        'cn_nlp': cn_nlp_dep,
        'vision': vision_dep,
        'leveldb': leveldb_dep,
        'test': test_dep,
        'all': all_dep,
    },
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
