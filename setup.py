from setuptools import setup, find_packages

setup(
    name="kaidos",
    version="0.2.0",
    description="A lightweight, educational blockchain and cryptocurrency implementation with UTXO model, proof-of-work mining, and P2P networking",
    author="jolovicdev",
    author_email="jolovicsharp@gmail.com",
    url="https://github.com/jolovicdev/kaidos",
    packages=find_packages(),
    install_requires=[
        "zenithdb>=2.0.0",
        "cryptography>=39.0.0",
        "flask>=2.2.0",
        "requests>=2.28.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "kaidos-wallet=Kaidos.cli.wallet_cli:main",
            "kaidos-node=Kaidos.cli.node_cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Security :: Cryptography",
        "Topic :: Education",
        "Topic :: Software Development :: Libraries",
        "Topic :: System :: Distributed Computing",
        "Topic :: Software Development :: Blockchain",
    ],
    python_requires=">=3.8",
)
