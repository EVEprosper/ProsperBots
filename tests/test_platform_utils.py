"""test_slack_utils.py: validate behavior/performance of slack_utils"""
from os import path
import json

import pytest
import helpers
import slackbot.slackclient as slackclient

import prosper_bots.platform_utils as platform_utils
import prosper_bots.exceptions as exceptions


HERE = path.abspath(path.dirname(__file__))
ROOT = path.abspath(path.join(path.dirname(HERE), 'prosper_bots'))
CACHE_PATH = path.join(HERE, 'cache')
