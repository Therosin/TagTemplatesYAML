from setuptools import setup, find_packages
import os
import shutil

with open("README.md", "r") as f:
    long_description = f.read()

if __name__ == "__main__":
    setup(
        name="TagTemplatesYAML",
        version="1.0",
        description="A useful module",
        license="MIT",
        long_description=long_description,
        author="Therosin",
        author_email="theros@svaltek,xyz",
        url="https:github.com/therosin/TagTemplatesYAML",
        packages=["TagTemplatesYAML"],
        install_requires=["pyyaml"],
    )
