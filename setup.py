#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='bfg',
    version='0.0.1',
    description='a load generator tool',
    longer_description='''
BFG is a modular load generator tool.
''',
    maintainer='Alexey Lavrenuke (load testing)',
    maintainer_email='direvius@gmail.com',
    url='https://github.com/direvius/bfg',
    packages=["bfg"],
    install_requires=[
        'hyper',
        'numpy',
        'pytoml',
    ],
    license='MIT',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Software Development :: Testing',
        'Topic :: Software Development :: Testing :: Traffic Generation',
        'Topic :: System :: Benchmark',
        'Programming Language :: Python :: 3',
    ],
    entry_points={
        'console_scripts': [
            'bfg = bfg.cli:main',
        ],
    },
    package_data={
        'bfg': ['config/*'],
    },
)
