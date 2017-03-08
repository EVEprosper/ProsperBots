"""remote.py: api helpers for public API feeds"""

from os import path
from datetime import datetime, timedelta
from enum import Enum

import ujson as json
import demjson
import requests
from tinydb import Query
from six.moves.html_parser import HTMLParser

from nltk import download
import nltk.sentiment as sentiment
import pandas_datareader.data as web

import prosper.common.prosper_logging as p_logging

DEFAULT_LOGGER = p_logging.DEFAULT_LOGGER

HERE = path.abspath(path.dirname(__file__))

LOADED_LEXICONS = []
def init_nltk(lexicon_name):
    """Make sure we can load the proper NLTK dependencies at load-time

    Args:
        lexicon_name (str): name of NLTK lexicon
        logger (:obj:`logging.logger`, optional): logging handle for errors

    Returns:
        (bool): pass/fail

    """
    global LOADED_LEXICONS

    if lexicon_name in LOADED_LEXICONS:
        #lexicon already loaded
        return True

    status = download(lexicon_name)

    if status:
        LOADED_LEXICONS.append(lexicon_name)
    else:
        raise NLTKLibraryDownloadFail('Unable to load lexicon: ' + lexicon_name)

    return status

NEWS_URI = 'https://www.google.com/finance/company_news'
def get_news(
        ticker,
        news_uri=NEWS_URI
):
    """Fetch news from google

    Note:
        google/yahoo disagree on some tickers swapping ./-
        uses demjson for parsing b/c google delivers bad JSON

    Args:
        ticker (str): stock ticker to evaluate
        news_uri (str, optional): override for API endpoint

    Returns:
        (:obj:`dict`)

    """
    params = {
        'q':ticker,
        'output':'json'
    }
    try:
        req = requests.get(
            news_uri,
            params=params
        )
        status = req.status_code
        req.raise_for_status()
    except requests.exceptions.HTTPError as err:
        if status == 404:
            raise EndpointDown(
                'Unable to resolve remote endpoint' +
                '\n\turl: {0}?q={1}&output=json'.format(news_uri, ticker) +
                '\n\tparams: {0}'.format(params)
            )
        if status == 400:
            raise EmptyNewsEndpoint(
                'No news found on endpoint' +
                '\n\turl: {0}'.format(req.url) +
                '\n\texc: {0}'.format(repr(err))
            )
    except Exception as err:    #pragma: no cover
        raise err

    #try:
    #    article_list = demjson.decode(req.text)
    #except Exception as err:
    #    raise err

    return demjson.decode(req.text)

def parse_google_news(
        news_obj,
        filtered_sources=[]
):
    """crunching google news endpoint can be tricky

    Args:
        news_obj (:obj:`dict`): raw object off google endpoint
        filtered_sources (:obj:`list` optional): sources to exclude

    Returns:
        (:obj:`list`) parsed and human-readable version of google news endpoint

    """
    articles = []
    for row in news_obj['clusters']:
        if int(row['id']) == -1:
            continue #last entry is weird

        for index, story in enumerate(row['a']):
            try:
                story_row = human_readable_article_data(
                    story,
                    index
                )
            except Exception as err_msg:
                raise StoryParseKeyError(
                    'Unable to parse article: ' +
                    repr(err_msg)
                )
            articles.append(story_row)

    return articles

def human_readable_article_data(
        news_story_row,
        story_index=-1
):
    """switch story info into more readable format

    Args:
        news_story_row (:obj:`dict`): single row from google endpoint
        story_index (int, optional): used for 'primary' keying
    Returns:
        (:obj:`dict`) reclassified and cleaned up object

    """
    article_row = {}
    parser = HTMLParser()

    article_row['source']   = news_story_row['s']
    article_row['url']      = news_story_row['u']
    article_row['title']    = parser.unescape(news_story_row['t'])
    article_row['blurb']    = parser.unescape(news_story_row['sp'])
    article_row['usg']      = news_story_row['usg'] #not sure if UUID is useful?
    article_row['datetime'] = datetime.\
        fromtimestamp(int(news_story_row['tt'])).\
        strftime('%Y-%m-%d %H:%M:%S')
    article_row['primary'] = False
    if story_index == 0:
        article_row['primary'] = True
    return article_row
    #Unused keys:
    #story_info['sru']  google reference link
    #story_info['d']    human-readable "when published" info

def grade_articles_vader(
    article_row
):
    """go over text data to grade entries with vader sentiment analyzer

    Args:
        article_row (:obj:`dict`): single article entry

    Returns:
        (:obj:`dict`) data section with graded segments

    """
    if 'vader_lexicon' not in LOADED_LEXICONS:
        raise NLTKLibraryNotLoaded('vader_lexicon not loaded yet')

    article_title = ''
    article_blurb = ''
    try:
        article_title = article_row['title']
        article_blurb = article_row['blurb']
    except KeyError:
        article_row = human_readable_article_data(article_row)
        article_title = article_row['title']
        article_blurb = article_row['blurb']

    text_analyzer = sentiment.vader.SentimentIntensityAnalyzer()
    data = {}
    data['title'] = text_analyzer.polarity_scores(article_title)
    data['blurb'] = text_analyzer.polarity_scores(article_blurb)

    return data


class MarketStatus(Enum):
    """enum for tracking market status"""
    OPEN = 1
    CLOSED = 2
    UNKNOWN = 3

def market_open(
        auth_key,
        cache_buster=False,
        calendar_cache=None,
        endpoint_url='https://api.tradier.com/v1/markets/calendar',
        logger=DEFAULT_LOGGER
):
    """check to see if the market is open today

    Note:
        uses https://developer.tradier.com/documentation/markets/get-calendar

    Args:
        auth_key (str): Tradier API key
        cache_buster (bool, optional): ignore cache, DEFAULT: False
        calendar_cache (:obj:`TinyDB`, optional): cached version of market calendar
        endpoint_url (str, optional): tradier endpoint (exposed for testing)
        logger (:obj:`logging.logger`): logger for tracking progress
    Returns:
        (bool): is market open?

    """
    logger.info('testing if market is open today')
    today = datetime.today().strftime('%Y-%m-%d')
    status = MarketStatus.UNKNOWN

    ## Check to see if we have the schedule already ##
    if (not cache_buster) and (calendar_cache is not None):
        status = check_calendar_cache(
            calendar_cache,
            logger
        )

    ## Get calendar from API ##
    calendar = {}
    if cache_buster or status == MarketStatus.UNKNOWN:
        calendar = fetch_tradier_calendar(
            auth_key,
            endpoint_url,
            logger
        )
        status = parse_tradier_calendar(
            calendar,
            today,
            logger
        )

    ## Write update to cache ##
    if (calendar_cache is not None) and calendar:
        update_calendar_cache(
            calendar_cache,
            calendar,
            logger
        )

    #TODO: test coverage?
    if status == MarketStatus.OPEN:
        return True
    else:
        return False

def parse_tradier_calendar(
        calendar_obj,
        today,
        logger=DEFAULT_LOGGER
):
    """parse calendar to find out if market is open today

    Args:
        calendar_obj (:obj:`dict`): raw output from tradier v1/markets/calendar
        today (str): datetime string %Y-%m-%d for searching tradier output
        logger (:obj:`logging.logger`, optional): logger for tracking progress

    Returns:
        (:enum:`MarketStatus`): current market status

    """
    status = MarketStatus.UNKNOWN
    date_info = {}
    for day in calendar_obj['calendar']['days']['day']:
        if day['date'] == today:
            date_info = day
            break   #stop searching when found
        else:
            continue

    if date_info:
        if date_info['status'] == 'open':
            status = MarketStatus.OPEN
        elif date_info['status'] == 'closed':
            status = MarketStatus.CLOSED
        else:
            logger.warning(
                'Unable to classify market status' +
                '\n\tstatus={0}'.format(date_info['status']) +
                '\n\tdate_info={0}'.format(date_info)
            )
            raise UnexpectedMarketStatus(
                '{0} is unhandled market status value'.format(date_info['status'])
            )
    else:
        logger.error(
            'EXCEPTION: unable to find date  info at Tradier' +
            '\n\tcalendar={0}'.format(calendar_obj) +
            '\n\ttoday={0}'.format(today)
        )
        raise UnexpectedMarketStatus('No information found for today')

    return status

def fetch_tradier_calendar(
        auth_key,
        endpoint_url='https://api.tradier.com/v1/markets/calendar',
        logger=DEFAULT_LOGGER
):
    """Fetch latest calendar from Tradier

    Args:
        auth_key (str): Tradier API key
        endpoint_url (str, optional): api URL path
        logger (:obj:`logging.logger`, optional): logger for tracking progress

    Returns:
        (:obj:`dict`) Tradier API response

    """
    logger.info('--checking internet for calendar')

    headers = {
        'Accept': 'application/json',
        'Authorization': 'Bearer ' + auth_key
    }
    try:
        req = requests.get(
            endpoint_url,
            headers=headers
        )
        req.raise_for_status()
        calendar = req.json()
    except Exception as err_msg:
        logger.error(
            'EXCEPTION: unable to fetch calendar' +
            '\n\turl={0}'.format(endpoint_url),
            exc_info=True
        )
        raise err_msg #TODO: no calendar behavior?

    return calendar

def check_calendar_cache(
        calendar_cache,
        logger=DEFAULT_LOGGER
):
    """look for current day inside existing calendar tinyDB

    Args:
        calendar_cache (:obj:`tinydb.tinyDB`): collection of tradier market calendar info
        logger (:obj:`logging.logger`): logging handle for debug stuff

    Returns:
        (:enum:MarketStatus) status of market today

    """
    logger.info('--checking cache')
    status = MarketStatus.UNKNOWN
    today = datetime.today().strftime('%Y-%m-%d')
    day_query = Query()

    cache_value = calendar_cache.search(day_query.date == today)
    if cache_value:
        logger.info('--found info in cache')
        if cache_value[0]['status'] == 'closed':
            logger.debug('----markets closed today')
            status = MarketStatus.CLOSED
        elif cache_value[0]['status'] == 'open':
            logger.debug('----markets open today')
            status = MarketStatus.OPEN
        else:
            #TODO: how to test?
            logger.error(
                'EXCEPTION: unexpected market status' +
                '\n\tcache_value={0}'.format(cache_value)
            )
            raise UnexpectedMarketStatus(
                'Could not resolve status ' +
                '\n\tstatus={0}'.format(cache_value[0]['status'])
            )

    return status

def update_calendar_cache(
        calendar_cache,
        update_payload,
        logger=DEFAULT_LOGGER
):
    """function for pushing updated information into cache

    Args:
        calendar_cache (:obj:`tinydb.TinyDB`): db with cached calendar info
        update_payload (:obj:`dict`): raw tradier output from v1/markets/calendar
        logger (:obj:`logging.logger`, optional): logger for tracking progress

    Returns:
        void

    """
    logger.info('--updating cache')
    calendar_update = update_payload['calendar']['days']['day']
    calendar_cache.insert_multiple(calendar_update)

class RemoteException(Exception):
    """base exception class for remote modules"""
    pass
class NLTKLibraryDownloadFail(Exception):
    """unable to load requested Lexicon"""
    pass
class NLTKLibraryNotLoaded(Exception):
    """required library not loaded"""
    pass
class EmptyNewsEndpoint(RemoteException):
    """exception for alerting when news RSS/json returns nothing"""
    pass
class EndpointDown(RemoteException):
    """wrapper for request errors, alert to stop parsing"""
    pass
class UnexpectedMarketStatus(RemoteException):
    """exception for alerting when market calendar reaches unknown state"""
    pass
class StoryParseKeyError(RemoteException):
    """exception for alerting when processing news articles fails"""
    pass
