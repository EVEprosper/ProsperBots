"""commands.py: generic responses for bots.  We make the responses"""
from os import path
import platform

from contexttimer import Timer

import prosper.datareader.coins as coins
import prosper.datareader.stocks as stocks

from . import _version
from . import connections
from . import utils
from . import exceptions
from . import config as api_config

HERE = path.abspath(path.dirname(__file__))

def version_info(app_name):
    """return version string for status checker

    Args:
        app_name (str): name of bot structure

    Returns:
        (str): {app_name} -- {version} -- {platform.node()}

    """
    return '{app_name} -- {version} -- {platform}'.format(
        app_name=app_name,
        version=_version.__version__,
        platform=platform.node()
    )

def generic_stock_info(
        ticker,
        db_conn,
        cooldown_time=30,
        info_mask=['name', 'current_price', 'change_pct'],
        logger=api_config.LOGGER
):
    """get generic stock information (company name, current price)

    Args:
        ticker (str): company ticker
        db_conn (:obj:`tinymongo.TinyMongoDatabase`): database to use
        cooldown_time (int, optional): anti-spam timeout
        info_mask (:obj:`list`, optional): what data to use from quote endpoint
        logger (:obj:`logging.logger`, optional): logging handle

    Returns:
        (str): {comany_name} {current_price} {change_pct}

    """
    ticker = ticker.upper()
    logger.info('Fetching stock info: %s', ticker)

    if connections.cooldown(
            'BASIC-{}'.format(ticker),
            db_conn,
            cooldown_time=cooldown_time,
            logger=logger
    ):
        logger.info('--called too quickly, shutting up')
        return ''

    with Timer as stock_info_timer:
        try:
            data = utils.get_basic_ticker_info(
                ticker,
                info_mask,
                logger=logger
            )
        except Exception:  # pragma: no cover
            logger.warning('unable to fetch basic ticker info', exc_info=True)
            data = ''

        logger.info('--basic stock quote timer: %s', stock_info_timer)

    return data

