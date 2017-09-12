"""connections.py: database and cache utilities for bot commands"""
from os import path
import time

from tinymongo import TinyMongoClient

import prosper_bots.config as api_config

CONN = TinyMongoClient('cache')['prosper']
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
