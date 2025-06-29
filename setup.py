from setuptools import setup

setup(
    name="EdboTools",
    version="0.1",
    description="A tool to build NMT results table for a university.",
    long_description="This project provides functionality to fetch and build a table of NMT results for a specified university.",
    long_description_content_type="text/markdown",
    url="https://github.com/seynyyy/EdboTools",
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
    packages=["edbo_tools", "CLI"],
    entry_points={
        "console_scripts": [
            "fetch-results=CLI.fetch_offers_results:main",
        ],
    },
    license='MIT License'
)