"""utils.py: generic functions that drive individual bot responses"""
from os import path
from enum import Enum
import time

import requests_cache
import pandas_datareader as pd_reader

import prosper.datareader.stocks as p_stocks
import prosper.datareader.coins as p_coins

import prosper_bots.config as api_config
#import prosper_bots.connections as connections

HERE = path.abspath(path.dirname(__file__))
#SESSION = requests_cache.CachedSession(
#    backend='memory',
#    expire_after=3600
#)
## Monkey patches ##
pd_reader.yahoo.quotes._yahoo_codes = {
    **pd_reader.yahoo.quotes._yahoo_codes,
    'company_name': 'n'
}


class Sources(Enum):
    """supported data sources"""
    pandas = 'pandas_datareader'
    robinhood = 'robinhood'
    hitbtc = 'hitBTC'

def get_basic_ticker_info(
        ticker,
        feed_elements,
        cache_time=30,
        #session=SESSION,
        source=Sources.pandas,  # TODO
        logger=api_config.LOGGER
):
    """look up basic info on a given stock or coin

    Args:
        ticker (str): name of product
        feed_elements (:obj:`list`): list of stuff to return
        session (:obj:`requests_cache.CachedSession`, optional): requests_cache
        source (:obj:`Enum`): enumerated Sources()
        logger (:obj:`logging.logger`, optional): logging hanlde

    Returns:
        (str): response for message

    """
    #return 'IN PROGRESS - {}'.format(ticker)
    logger.info('--fetching quote data from yahoo')
    data = pd_reader.get_quote_yahoo(
        ticker,
        #session
    )

    if data.get_value(ticker, 'company_name') == 'N/A':
        coin = ticker + 'USD=X'
        logger.info('--ticker not found, trying coin %s', coin)
        data = pd_reader.get_quote_yahoo(
            coin,
            #session
        )
        ticker = coin
        if data.get_value(coin, 'company_name') == 'N/A':
            logger.warning('--unable to resolve ticker %s', ticker)
            return ''

    return ' '.join(list(map(str, data.loc[ticker, feed_elements])))
