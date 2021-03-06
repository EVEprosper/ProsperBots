"""commands.py: generic responses for bots.  We make the responses"""
from os import path
import platform

from contexttimer import Timer

import prosper.datareader.coins as coins
import prosper.datareader.stocks as stocks
import prosper.datareader.news as news
import prosper.datareader.utils as pdr_utils

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
            'BASIC_STOCKS-{}'.format(ticker),
            db_conn,
            cooldown_time=cooldown_time,
            logger=logger
    ):
        logger.info('--called too quickly, shutting up')
        return ''

    with Timer() as stock_info_timer:
        try:
            raw_data = stocks.get_quote_rh(ticker)
            data = ' '.join(list(map(str, raw_data.loc[0, info_mask])))
        except Exception:  # pragma: no cover
            logger.warning('unable to fetch basic ticker info', exc_info=True)
            data = ''

        logger.info('--basic stock quote timer: %s', stock_info_timer)

    return data

def generic_coin_info(
        ticker,
        db_conn,
        currency='USD',
        cooldown_time=30,
        info_mask=['name', 'last', 'change_pct'],
        logger=api_config.LOGGER
):
    """get generic coin information (current price)

    Args:
        ticker (str): coin ticker
        db_conn (:obj:`tinymongo.TinyMongoDatabase`): database to use
        currency (str): currenct to FOREX against
        cooldown_time (int, optional): anti-spam timeout
        info_mask (:obj:`list`, optional): what data to use from quote endpoint
        logger (:obj:`logging.logger`, optional): logging handle

    Returns:
        (str): {comany_name} {current_price} {change_pct}

    """
    coin_ticker = ticker.upper() + currency
    logger.info('Fetching coin info: %s', ticker)

    if connections.cooldown(
            'BASIC_COINS-{}'.format(coin_ticker),
            db_conn,
            cooldown_time=cooldown_time,
            logger=logger
    ):
        logger.info('--called too quickly, shutting up')
        return ''

    with Timer() as coin_info_timer:
        try:
            raw_data = coins.get_quote_cc(
                [ticker],
                logger=logger,
                currency=currency,
                to_yahoo=True
            )
            logger.debug(raw_data)
            data = ' '.join(list(map(str, raw_data.loc[ticker, info_mask])))
        except Exception:
            logger.warning('unable to fetch basic coin info: %s', coin_ticker, exc_info=True)
            data = ''

        logger.info('--basic coin quote timer: %s', coin_info_timer)

        return data

def stock_news(
        ticker,
        direction,
        logger=api_config.LOGGER
):
    """generate news along with quote

    Args:
        ticker (str): coin ticker
        direction (float): change_pct value +/-
        info_mask (:obj:`list`, optional): what data to use from quote endpoint
        logger (:obj:`logging.logger`, optional): logging handle

    Returns:
        str: link to "best" article
        str: additional info

    """
    #if isinstance(direction, str):
    #    direction = float(direction.split()[-1].replace('%', ''))

    logger.info('--fetching news')
    with Timer() as stock_news_timer:
        try:
            news_df = news.company_news_rh(ticker, logger=logger)
            news_df = pdr_utils.vader_sentiment(news_df, 'title', logger=logger)
        except KeyError as err:
            logger.warning('Blank feed found', exc_info=True)
            return 'NO NEWS FOUND',''
        except Exception as err:
            logger.warning('unable to fetch news for ticker %s', ticker, exc_info=True)
            return 'ERROR - UNABLE TO FETCH NEWS FOR {} - {}'.format(
                ticker, repr(err)
            ), ''

        logger.debug(news_df.head(5))
        logger.info('--news fetch timer: %s', stock_news_timer)

    if direction > 0:
        logger.info('--finding positive news')
        best_article = news_df[news_df['compound'] == max(news_df['compound'])]
        logger.debug(best_article)
        url = best_article.iloc[0]['url']
        score = best_article.iloc[0]['compound']

    elif direction < 0:
        logger.info('--finding negative news')
        best_article = news_df[news_df['compound'] == min(news_df['compound'])]
        logger.debug(best_article)
        url = best_article.iloc[0]['url']
        score = best_article.iloc[0]['compound']

    else:  # pragma no cover
        #TODO: raise EmptyQuoteReturned?
        url = ''
        score = ''

    logger.info('--best article: %s (%s)', url, score)
    return str(url), str(score)

def generate_candlestick_stocks(
        ticker,
        range=60,
        logger=api_config.LOGGER
):
    """build an OHLC candlestick plot for a requested stock

    Notes:
        Uses IEX sources

    Args:
        ticker (str): ticker of company to generate plot from
        range (int, optional): days to include in plot
        logger (:obj:`logging.logger`, optional): logging handle

    Returns:
        str: link to generated plot

    """
    pass
