#!/usr/bin/env python

from setuptools import setup

setup(
    name='ftp2http',
    version='0.3.1',
    description='FTP to HTTP server',
    author='Raymond Butcher',
    author_email='randomy@gmail.com',
    url='https://github.com/apn-online/ftp2http',
    license='MIT',
    packages=(
        'ftp2http',
    ),
    scripts=(
        'bin/ftp2http',
    ),
    install_requires=(
        'argparse',
        'pyftpdlib',
        'pyOpenSSL',
        'python-bcrypt',
        'python-swiftclient==1.9.0',
    ),
)
