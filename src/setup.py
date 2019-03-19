from setuptools import setup, find_packages
from setuptools.extension import Extension

setup(
    name='nes',
    packages=find_packages(),
    version='0.0.1',
    zip_safe=False,
    setup_requires=[
        'setuptools>=18.0',
        'cython',
    ],
    ext_modules=[
        Extension(
            'nes.cython_core',
            ['cython_core/bindex.pyx'],
            extra_compile_args=['-O3'],
        ),
    ],
    install_requires=[
        'termcolor>=1.1'
    ],
    extras_require={
        'test': ['numpy'],
    },
)
