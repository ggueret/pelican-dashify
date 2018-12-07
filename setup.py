import os
from setuptools import setup

BASEDIR_PATH = os.path.abspath(os.path.dirname(__file__))

setup(
    name="pelican-dashify",
    version=open(os.path.join(BASEDIR_PATH, "VERSION"), "r").read().rstrip(),
    author="Geoffrey GUERET",
    author_email="geoffrey@stocka.net",

    description="Pelican-dashify allows you to convert proper MPEG-DASH content generated from your videos with Pelican.",
    long_description=open(os.path.join(BASEDIR_PATH, "README.md"), "r").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/ggueret/pelican-dashify",
    license="MIT",

    packages=["pelican_dashify"],
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*",
    install_requires=["pelican>=3.7"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Framework :: Pelican",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Multimedia :: Video :: Conversion",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ]
)
