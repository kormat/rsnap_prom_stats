#!/usr/bin/python3

from setuptools import setup, find_packages
setup(
    name="rsnap_prom_stats",
    version="0.1",
    description="Extracts stats from rsnapshot for Prometheus",
    license="Apache 2.0",
    url="https://github.com/kormat/rsnap_prom_stats",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'rsnap_prom_stats = rsnap_prom_stats:main',
        ],
    }
)
