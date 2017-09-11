"""slackbot_settings.py: as-perscribed config home for slackbot args"""
from os import path

import prosper.common.prosper_config as p_config

HERE = path.abspath(path.dirname(__file__))
CONFIG = p_config.ProsperConfig(path.join(HERE, 'bot_config.cfg'))

DEFAULT_REPLY = 'I am a pretty bot'

ERRORS_TO = CONFIG.get('SlackBot', 'error_dest')

API_TOKEN = CONFIG.get('SlackBot', 'api_token')
