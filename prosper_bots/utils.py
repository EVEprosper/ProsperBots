"""utils.py: generic functions that drive individual bot responses"""
from os import path
from enum import Enum
import time

import requests_cache

import prosper.datareader.stocks as stocks
import prosper.datareader.coins as coins

import prosper_bots.config as api_config
#import prosper_bots.connections as connections

HERE = path.abspath(path.dirname(__file__))

class Modes(Enum):
    """channel modes"""
    stocks = 'stocks'
    coins = 'coins'

class Sources(Enum):
    """supported data sources"""
    robinhood = 'robinhood'
    hitbtc = 'hitBTC'
