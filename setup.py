#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='bfg',
    version='0.1.0',
    description='a load generation tool and framework',
    longer_description='''
BFG is a modular tool and framework for load generation.
''',
    maintainer='Alexey Lavrenuke (load testing)',
    maintainer_email='direvius@gmail.com',
    url='https://github.com/direvius/bfg',
    packages=find_packages(exclude=["tests", "tmp", "docs", "data"]),
    install_requires=[
        'hyper',
        'numpy',
        'pandas',
        'PyYAML',
        'pytoml',
        'arrow',
        # 'python-spdylay',
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
