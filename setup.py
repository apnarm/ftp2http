#!/usr/bin/env python


from glob import glob


from setuptools import setup, find_packages


def parse_requirements(filename):
    with open(filename, "r") as f:
        for line in f:
            if line and line[:2] not in ("#", "-e"):
                yield line.strip()


setup(
    name="ftp2http",
    description="FTP to HTTP server",
    long_description=open("README.rst", "r").read(),
    author="APN Online",
    author_email="dev.admin@apnonline.com.au",
    url="https://github.com/apnarm/ftp2http",
    license="MIT",
    packages=find_packages("."),
    scripts=glob("bin/*"),
    install_requires=list(parse_requirements("requirements.txt")),
    entry_points={
        "console_scripts": [
            "ftp2http=ftp2http.__main__:main",
        ]
    },
    zip_safe=True,
    use_scm_version={
        "write_to": "ftp2http/version.py",
    },
    setup_requires=[
        "setuptools_scm"
    ],
)
