from setuptools import setup

setup(
    name="FetchNmtResults",
    version="0.1",
    description="A tool to build NMT results table for a university.",
    long_description="This project provides functionality to fetch and build a table of NMT results for a specified university.",
    long_description_content_type="text/markdown",
    url="https://github.com/seynyyy/FetchAbiturientsResults",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        "requests>=2.25.1",
    ],
    author="seynyyy",
    packages=["fetch_data"],
    entry_points={
        "console_scripts": [
            "fetch-results=fetch_data.main:main",
        ],
    },
)