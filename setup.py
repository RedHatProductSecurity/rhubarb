from urllib.parse import urljoin

from setuptools import find_packages, setup

import rhubarb

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="rhubarb",
    version=rhubarb.__version__,
    author=rhubarb.__author__,
    author_email=rhubarb.__contact__,
    description="Avoid running multiple instances of the same celery task concurrently",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=rhubarb.__homepage__,
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Environment :: Plugins",
        "Framework :: Celery",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries",
        "Topic :: System :: Distributed Computing",
    ],
    keywords=rhubarb.__keywords__,
    project_urls={
        "Source": rhubarb.__homepage__,
        "Tracker": urljoin(rhubarb.__homepage__, "issues"),
    },
    packages=find_packages(exclude=("tests",)),
    install_requires=[
        "celery>=5.2.0",
        "redis>=4.5.0",
    ],
    python_requires=">=3.8",
)
