"""connections.py: database and cache utilities for bot commands"""
from os import path
import time
from enum import Enum
from datetime import datetime, timedelta

from tinymongo import TinyMongoClient
import pandas as pd

from . import config as api_config
from . import exceptions
import prosper.datareader.coins.info as info

HERE = path.abspath(path.dirname(__file__))

class Modes(Enum):
    """channel modes"""
    stocks = 'stocks'
    coins = 'coins'
    test = 'TEST'

def build_connection(
        source_name,
        source_path=path.join(HERE, 'cache'),
        logger=api_config.LOGGER
):
    """create a connection object for a bot main() to reference

    Args:
        source_name (str): name of db
        source_path (str, optional): path to db
        logger (:obj:`logging.logger`, optional): logging handle

    Returns:
        (:obj:`tinymongo.TinyMongoDatabase`): handle to database

    """
    logger.info('Building db connection: %s', path.join(source_path, source_name + '.json'))

    return TinyMongoClient(source_path)[source_name]

CHANNEL_COLLECTION = 'channel_settings'
DEFAULT_MODE = Modes.stocks
def check_channel_mode(
        channel_name,
        db_conn,
        channel_mode_collection=CHANNEL_COLLECTION,
        default_mode=DEFAULT_MODE,
        logger=api_config.LOGGER
):
    """figure out the mode of a given channel

    Args:
        channel_name (str): name of channel (guid > pretty-string)
        db_conn (:obj:`tinymongo.TinyMongoDatabase`): database to use
        channel_mode_collection (str, optional): name of collection to query
        default_mode (str, optional): expected mode
        logger (:obj:`logging.logger`, optional): logging handle

    Returns:
        (:obj:`Enum`): channel mode

    """
    logger.info('Checking channel mode for %s', channel_name)
    mode_res = list(db_conn[channel_mode_collection].\
        find({'channel_name': channel_name}))

    if len(mode_res) > 1:
        logger.warning('Too many options returned, confused')
        logger.debug(mode_res)
        raise exceptions.TooManyOptions(
            'channel_mode returned {}, expected <1'.format(len(mode_res)))

    if not mode_res:
        logger.info('--no mode found, using default: %s', default_mode.value)
        return default_mode

    channel_mode = mode_res[0]['channel_mode']
    logger.info('--channel mode %s', channel_mode)
    set_mode = Modes(channel_mode)  # validate option is supported
    return set_mode

def set_channel_mode(
        channel_name,
        channel_mode,
        user_name,
        db_conn,
        channel_mode_collection=CHANNEL_COLLECTION,
        logger=api_config.LOGGER
):
    """set expected mode for channel

    Args:
        channel_name (str): name of channel (guid > pretty-string)
        channel_mode (str): what mode to set the channel to
        user_name (str): who is setting the channel mode
        db_conn (:obj:`tinymongo.TinyMongoDatabase`): database to use
        channel_mode_collection (str, optional): name of collection to query
        logger (:obj:`logging.logger`, optional): logging handle
    Returns:
        (:obj:`Enum`): channel mode

    """
    set_mode = Modes(channel_mode)  # validate option is supported
    logger.info('Setting channel %s to %s mode', channel_name, channel_mode)

    current_mode_res = list(db_conn[channel_mode_collection].\
        find({'channel_name': channel_name}))

    if current_mode_res:
        logger.info('--current mode found: %s', current_mode_res[0]['channel_mode'])
        if len(current_mode_res) > 1:
            logger.warning('Too many options returned, confused')
            logger.debug(current_mode_res)
            raise exceptions.TooManyOptions(
                'channel_mode returned {}, expected <1'.format(len(current_mode_res)))

    logger.info('--cleaning up collection')
    db_conn[channel_mode_collection].delete_many({'channel_name': channel_name})

    logger.info('--setting up channel mode')
    channel_mode_obj = {
        'channel_name': channel_name,
        'channel_mode': channel_mode,
        'channel_set_time': datetime.utcnow().isoformat(),
        'user_name': user_name
    }
    logger.debug(channel_mode_obj)
    db_conn[channel_mode_collection].insert_one(channel_mode_obj)

    return set_mode


COOLDOWN_COLLECTION = 'cooldown'
def cooldown(
        element_name,
        db_conn,
        cooldown_time=30,
        cooldown_collection=COOLDOWN_COLLECTION,
        logger=api_config.LOGGER
):
    """avoids spam by shushing for ``cooldown_time`` seconds

    Args:
        element_name (str): name of element (usually "SOURCE-THING")
        db_conn (:obj:`tinymongo.TinyMongoDatabase`): database to use
        cooldown_time (int, optional): time to shut up (seconds)
        cooldown_collection (str, optional): name of collection to track cache
        logger (:obj:`logging.logger`, optional): logging handle

    Returns:
        (bool): should you keep silent?
    Raises:
        FileError: can't make a cache file

    """
    if cooldown_time <= 0:  # pragma: no cover
        return

    logger.info('--checking cooldown cache for %s', element_name)
    cache_element = db_conn[cooldown_collection].find_one({'element_name': element_name})

    sleep_time = cooldown_time
    if cache_element:
        logger.debug('--found timer')
        sleep_time = time.time() - cache_element['time']

    if sleep_time < cooldown_time:
        return True

    logger.info('--cleaning up cooldown cache')
    db_conn[cooldown_collection].delete_many({'element_name': element_name})
    db_conn[cooldown_collection].insert_one({
        'element_name': element_name,
        'time': time.time()
    })

    return False

COINS_COLLECTION = 'coins'
def check_coins(
        ticker,
        db_conn,
        cache_buster=False,
        cache_age=86400,
        coins_collection=COINS_COLLECTION,
        logger=api_config.LOGGER
):
    """checks if ticker is a crypto-coin

    Args:
        ticker (str): name of product to check
        db_conn (:obj:`tinymongo.TinyMongoDatabase`): database to use
        cache_buster (bool, optional): skip cache
        logger (:obj:`logging.logger`, optional): logging handle

    Returns:
        (bool): coin or not

    """
    cache_time = time.time()

    logger.info('--checking cache for %s', ticker)
    cached_data = list(db_conn[coins_collection].find(
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
        db_conn[coins_collection].delete_many({})

        logger.info('--rebuilding cache')
        db_conn[coins_collection].insert_many(coin_cache)

    else:
        logger.info('--reading cached values')
        coins_df = pd.DataFrame(cached_data)
        coins_list = list(coins_df['coin_ticker'])

    return ticker in coins_list
