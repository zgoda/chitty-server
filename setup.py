import ast
import codecs
import re
from os import path

from setuptools import find_packages, setup

here = path.abspath(path.dirname(__file__))


def read(*parts):
    with codecs.open(path.join(here, *parts), "r") as fp:
        return fp.read()


_version_re = re.compile(r"__version__\s+=\s+(.*)")


def find_version(*where):
    match = _version_re.search(read(*where))
    if match:
        return str(ast.literal_eval(match.group(1)))
    return "0.0.0"


base_reqs = [
    "trio",
    "trio-websocket",
    "redio",
    "falcon",
    "redis[hiredis]",
    "passlib[argon2]",
    "itsdangerous",
    "python-dotenv",
    'cached-property ; python_version<"3.8"',
]

test_reqs = [
    "pytest",
    "pytest-cov",
    "pytest-trio",
    "pytest-mock",
]

docs_reqs = [
    "Sphinx",
    "furo",
]

dev_reqs = (
    [
        "werkzeug[watchdog]",
        "ipython",
        "ipdb",
        "wheel",
        "flake8",
        "flake8-builtins",
        "flake8-bugbear",
        "flake8-comprehensions",
        "pep8-naming",
        "dlint",
        "rstcheck",
        "rope",
        "isort",
        "black",
    ]
    + test_reqs
    + docs_reqs
)

setup(
    name="chitty",
    version=find_version("src", "chitty", "__init__.py"),
    author="Jarek Zgoda",
    author_email="jarek.zgoda@gmail.com",
    description="Chat and more",
    long_description=read("README.rst"),
    long_description_content_type="text/x-rst",
    license="BSD",
    packages=find_packages("src"),
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
    url="http://github.com/zgoda/chitty-server",
    project_urls={
        "Source": "https://github.com/zgoda/chitty-server",
        "Issues": "https://github.com/zgoda/chitty-server/issues",
    },
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Web Environment",
        "Framework :: Trio",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Communications :: Chat",
    ],
    install_requires=base_reqs,
    extras_require={
        "dev": dev_reqs,
        "test": test_reqs,
        "docs": docs_reqs,
    },
    entry_points={
        "console_scripts": [
            "chitty=chitty.cli:run",
            "web=chitty.web.cli:main",
        ]
    },
    python_requires="~=3.7",
)
