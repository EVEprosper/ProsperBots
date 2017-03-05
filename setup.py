"""wheel setup for Prosper bots"""

from os import path, listdir
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

HERE = path.abspath(path.dirname(__file__))
__version__ = '0.0.1'
#__project_name__ = 'bots'

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
            'Tests',
            '--cov=prosper/',
            '--cov-report=term-missing'
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
    name='ProsperBots',
    author='John Purcell',
    author_email='prospermarketshow@gmail.com',
    url='https://github.com/EVEprosper/ProsperBots',
    download_url='https://github.com/EVEprosper/ProsperBots/tarball/v' + __version__,
    version=__version__,
    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 3.5'
    ],
    keywords='prosper eveonline api CREST',
    packages=hack_find_packages('prosper'),
    include_package_data=True,
    data_files=[
        ('Tests', include_all_subfiles('Tests')),
        ('Docs', include_all_subfiles('Docs')),
        ('Scripts', include_all_subfiles('Scripts'))
    ],
    package_data={
        'prosper':[
            'DiscordBot/discord_config.cfg',
            'SlackBot/slackbot_config.cfg'
        ]
    },
    install_requires=[
        'requests~=2.13.0',
        'ProsperCommon~=0.4.0',
        'ujson~=1.35',
        'tinydb~=3.2.1',
        'demjson~=2.2.4',
        'discord.py~=0.13.0',
        'nltk~=3.2.1',
        'pandas-datareader~=0.2.1',
        'slackbot~=0.4.1'
    ],
    tests_require=[
        'pytest~=3.0.0',
        'pytest_cov~=2.4.0',
    ],
    cmdclass={
        'test':PyTest
    }
)
