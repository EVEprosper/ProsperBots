"""utils.py: generic functions that drive individual bot responses"""
from os import path
from enum import Enum

HERE = path.abspath(path.dirname(__file__))


class Modes(Enum):
    """channel modes"""
    stocks = 'stocks'
    coins = 'coins'


class Sources(Enum):
    """supported data sources"""
    robinhood = 'robinhood'
    hitbtc = 'hitBTC'
