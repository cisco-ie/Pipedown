import os

from codecs import open
from setuptools import setup
from setuptools import find_packages

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'requirements.txt'), encoding='utf-8') as fp:
    requirements = fp.read().splitlines()

setup(
    name='Pipedown',
    version='1.2.1',
    author='Lisa Roach, Karthik Kumaravel',
    author_email='lisroach@cisco.com, kkumara3@cisco.com',
    url='https://github.com/cisco-ie/Pipedown',
    description='''
            Detects if a PoP router's connection to the home data center is lost.
            If lost, it removes its BGP relationship to the internet to prevent
            serving static content. If the link health improves, it adds itself
            back.
    ''',
    license='Apache-2',
    packages=find_packages(),
    install_requires=requirements
)
