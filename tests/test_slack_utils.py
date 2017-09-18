"""test_slack_utils.py: validate behavior/performance of slack_utils"""
from os import path
import json

import pytest
import helpers
import slackbot.slackclient as slackclient

import prosper_bots.slack_utils as slack_utils
import prosper_bots.exceptions as exceptions


class DummyMessage(object):
    """dummy slackbot.message framework"""
    def __init__(self, client):
        pass

class DummyClient(slackclient.SlackClient):
    """dummy slacker.slacker framework"""
    def __init__(self, token, bot_icon=None, bot_emoji=None, connect=False):
        """override base class __init__"""
        self.token = token
        self.bot_icon = bot_icon
        self.bot_emoji = bot_emoji
        self.username = None
        self.domain = None
        self.login_data = None
        self.websocket = None
        self.users = {}
        self.channels = {}
        self.connected = False
        self.webapi = None

    def parse_login_data_from_file(self, file_name):
        """read a cached version to load client info"""
        with open(path.join(HERE, file_name), 'r') as client_fh:
            data = json.load(client_fh)

        self.parse_slack_login_data(data)

DUMMY_CLIENT = DummyClient('DUMMY-TOKEN')
DUMMY_CLIENT.parse_login_data_from_file('slack_client.json')
