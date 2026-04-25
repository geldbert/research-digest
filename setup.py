from setuptools import setup, find_packages

setup(
    name="research-digest",
    version="0.1.8",
    author="geldbert",
    description="Generate curated research digests from arXiv and RSS feeds.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/geldbert/research-digest",
    packages=find_packages(exclude=["tests*"]),
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "research-digest=research_digest.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
    ],
)
