# -*- coding: utf-8 -*-
"""
AI-Platform: 个人AI自学与创作系统
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="ai-platform",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="个人AI自学与创作系统 - 七步法框架 + 编剧双赛道",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/caihongke/ai-knowledge-system",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "akm=cli.main:app",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.yaml", "*.json", "*.txt"],
    },
)