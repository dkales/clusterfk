from setuptools import setup

with open('requirements.txt') as fp:
    install_requires = fp.read()

setup(
    name='clusterfk',
    version='1.0',
    packages=['clusterfk'],
    install_requires=install_requires,
    url='https://github.com/dkales/clusterfk',
    license='',
    author='Daniel Kales, Vanessa Sereinig',
    author_email='daniel.kales@iaik.tugraz.at',
    description='A differential clustering tool for tweakable block ciphers.',
)