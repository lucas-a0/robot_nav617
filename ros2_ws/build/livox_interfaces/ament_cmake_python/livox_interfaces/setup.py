from setuptools import find_packages
from setuptools import setup

setup(
    name='livox_interfaces',
    version='0.0.0',
    packages=find_packages(
        include=('livox_interfaces', 'livox_interfaces.*')),
)
