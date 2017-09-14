"""wheel setup for Prosper Bot framework"""
from codecs import open
import importlib
from os import path, listdir

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

HERE = path.abspath(path.dirname(__file__))
__package_name__ = 'ProsperBots'
__library_name__ = 'prosper_bots'

def get_version(package_name):
    """find __version__ for making package

    Args:
        package_path (str): path to _version.py folder (abspath > relpath)

    Returns:
        (str) __version__ value

    """
    module = package_name + '._version'
    package = importlib.import_module(module)

    version = package.__version__

    return version

def hack_find_packages(include_str):
    """patches setuptools.find_packages issue

    setuptools.find_packages(path='') doesn't work as intended

    Returns:
        (:obj:`list` :obj:`str`) append <include_str>. onto every element of setuptools.find_pacakges() call

    """
    new_list = [include_str]
    for element in find_packages(include_str):
        new_list.append(include_str + '.' + element)

    return new_list

def include_all_subfiles(*args):
    """Slurps up all files in a directory (non recursive) for data_files section

    Note:
        Not recursive, only includes flat files

    Returns:
        (:obj:`list` :obj:`str`) list of all non-directories in a file

    """
    file_list = []
    for path_included in args:
        local_path = path.join(HERE, path_included)

        for file in listdir(local_path):
            file_abspath = path.join(local_path, file)
            if path.isdir(file_abspath):    #do not include sub folders
                continue
            file_list.append(path_included + '/' + file)

    return file_list

class PyTest(TestCommand):
    """PyTest cmdclass hook for test-at-buildtime functionality

    http://doc.pytest.org/en/latest/goodpractices.html#manual-integration

    """
    user_options = [('pytest-args=', 'a', "Arguments to pass to pytest")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = [
            'tests',
            '-rx',
            '--cov=' + __library_name__,
            '--cov-report=term-missing',
            '--cov-config=.coveragerc'
        ]    #load defaults here

    def run_tests(self):
        import shlex
        #import here, cause outside the eggs aren't loaded
        import pytest
        pytest_commands = []
        try:    #read commandline
            pytest_commands = shlex.split(self.pytest_args)
        except AttributeError:  #use defaults
            pytest_commands = self.pytest_args
        errno = pytest.main(pytest_commands)
        exit(errno)

setup(
    name=__package_name__,
    author='John Purcell',
    author_email='prospermarketshow@gmail.com',
    url='https://github.com/EVEprosper/' + __package_name__,
    download_url='https://github.com/EVEprosper/' + __package_name__ + '/tarball/v' + get_version(__library_name__),
    version=get_version(__library_name__),
    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 3.5'
    ],
    keywords='prosper nltk discord chat bot slack stocks',
    packages=find_packages(__library_name__),
    include_package_data=True,
    data_files=[
        ('tests', include_all_subfiles('tests')),
        ('docs', include_all_subfiles('docs')),
        ('scripts', include_all_subfiles('scripts'))
    ],
    package_data={
        '': ['LICENSE', 'README.rst'],
        'prosper-bots': ['version.txt']
    },
    install_requires=[
        'ProsperCommon~=1.1.1',
        'ProsperDatareader[nltk]~=1.1.3',
        'tinydb~=3.4.1',
        'tinymongo~=0.1.9',
        'discord.py~=0.16.10',
        'slackbot~=0.5.1',
        'plumbum~=1.6.3',
        'pandas~=0.20.3',
        'pandas_datareader~=0.5.0',
        'requests-cache~=0.4.13',
        'contexttimer~=0.3.3',
        'plotnine~=0.2.1'
    ],
    tests_require=[
        'pytest~=3.0.0',
        'pytest_cov~=2.4.0',
    ],
    extras_require={
        'dev':[
            'pandas-datareader',
            'sphinx',
            'sphinxcontrib-napoleon',
            'semantic-version'
        ]
    },
    cmdclass={
        'test':PyTest
    }
)
