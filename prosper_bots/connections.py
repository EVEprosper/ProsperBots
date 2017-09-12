"""connections.py: database and cache utilities for bot commands"""
from os import path
import time
#from datetime import datetime, timedelta

from tinymongo import TinyMongoClient
import pandas as pd

import prosper_bots.config as api_config
import prosper.datareader.coins.info as info

HERE = path.abspath(path.dirname(__file__))
CONN = TinyMongoClient(path.join(HERE, 'cache'))['prosper']

COOLDOWN_COLLECTION = 'cooldown'
def cooldown(
        element_name,
        cooldown_time=30,
        cooldown_collection=COOLDOWN_COLLECTION,
        logger=api_config.LOGGER
):
    """avoids spam by shushing for ``cooldown_time`` seconds

    Args:
        element_name (str): name of element (usually "SOURCE-THING")
        cooldown_time (int, optional): time to shut up (seconds)
        cooldown_collection (str, optional): name of collection to track cache
        logger (:obj:`logging.logger`, optional): logging handle

    Returns:
        (bool): should you keep silent?
    Raises:
        FileError: can't make a cache file

    """
    logger.info('--checking cooldown cache for %s', element_name)
    cache_element = CONN[cooldown_collection].find_one({'element_name': element_name})

    sleep_time = cooldown_time
    if cache_element:
        logger.debug('--found timer')
        sleep_time = time.time() - cache_element['time']

    if sleep_time < cooldown_time:
        return True

    logger.info('--cleaning up cooldown cache')
    CONN[cooldown_collection].delete_many({'element_name': element_name})
    CONN[cooldown_collection].insert_one({
        'element_name': element_name,
        'time': time.time()
    })

    return False

COINS_COLLECTION = 'coins'
def check_coins(
        ticker,
        cache_buster=False,
        cache_age=86400,
        coins_collection=COINS_COLLECTION,
        logger=api_config.LOGGER
):
    """checks if ticker is a crypto-coin

    Args:
        ticker (str): name of product to check
        cache_buster (bool, optional): skip cache
        logger (:obj:`logging.logger`, optional): logging handle

    Returns:
        (bool): coin or not

    """
    cache_time = time.time()

    logger.info('--checking cache for %s', ticker)
    cached_data = list(CONN[coins_collection].find(
        {'cache_time': {'$gt': cache_time - cache_age}}
    ))

    coins_list = []
    if not cached_data or cache_buster:
        ## Refresh cache ##
        logger.info('--fetching coin info')
        coins_list = info.supported_symbol_info('commodity')
        coins_df = pd.DataFrame(coins_list, columns=['coin_ticker'])
        coins_df['cache_time'] = cache_time
        coin_cache = list(coins_df.to_dict(orient='records'))

        logger.info('--clearing cache')
        CONN[coins_collection].delete_many({})

        logger.info('--rebuilding cache')
        CONN[coins_collection].insert_many(coin_cache)

    else:
        logger.info('--reading cached values')
        coins_df = pd.DataFrame(cached_data)
        coins_list = list(coins_df['coin_ticker'])

    return ticker in coins_list
