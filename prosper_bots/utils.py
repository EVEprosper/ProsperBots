"""utils.py: generic functions that drive individual bot responses"""
from os import path
from enum import Enum
import time

import requests_cache
import pandas_datareader as pd_reader

import prosper.datareader.stocks as stocks
import prosper.datareader.coins as coins

import prosper_bots.config as api_config
#import prosper_bots.connections as connections

HERE = path.abspath(path.dirname(__file__))

## Monkey patches ##
pd_reader.yahoo.quotes._yahoo_codes = {
    **pd_reader.yahoo.quotes._yahoo_codes,
    'company_name': 'n'
}

class Modes(Enum):
    """channel modes"""
    stocks = 'stocks'
    coins = 'coins'

class Sources(Enum):
    """supported data sources"""
    pandas = 'pandas_datareader'
    robinhood = 'robinhood'
    hitbtc = 'hitBTC'
