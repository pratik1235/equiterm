from setuptools import setup, find_packages

setup(
    name="equiterm",
    version="0.1.0",
    description="A terminal-based stock market application using Textual",
    author="Equiterm Team",
    packages=find_packages(),
    install_requires=[
        "textual>=0.40.0",
        "jugaad-data>=0.25",
        "requests>=2.31.0",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "equiterm=equiterm.app:main",
        ],
    },
)
