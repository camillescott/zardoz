#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ['discord.py',
                'rich',
                'dice',
                'pyyaml',
                'xdg',
                'aiofiles',
                'aiosql',
                'aiosqlite']

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest>=3', ]

setup(
    author="Camille Scott",
    author_email='cswel@ucdavis.edu',
    python_requires='>=3.6',
    entry_points={
        'console_scripts': [
            'zardoz = zardoz:main'
        ]
    },
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Another dice bot for discord.",
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='zardoz',
    name='zardoz',
    packages=find_packages(include=['zardoz', 'zardoz.*']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/camillescott/zardoz',
    version='0.8.1',
    zip_safe=False,
)
