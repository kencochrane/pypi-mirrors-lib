from distutils.core import setup

from pypimirrors import __version__

setup(
    name='pypi-mirrors',
    version=__version__,
    packages=['pypimirrors'],
    url='http://github.com/kencochrane/pypi-mirrors-lib',
    license='MIT',
    author='Ken Cochrane',
    author_email='KenCochrane@gmail.com',
    description='pypi mirror status library'
)
