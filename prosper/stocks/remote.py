"""remote.py: api helpers for public API feeds"""

from os import path
from datetime import datetime, timedelta

import ujson as json
import demjson
import requests

from nltk import download
import nltk.sentiment as sentiment
import pandas_datareader.data as web

import prosper.common.prosper_logging as p_logging

LOGGER = p_logging.DEFAULT_LOGGER

HERE = path.abspath(path.dirname(__file__))

def init_nltk(lexicon_name):
    """Make sure we can load the proper NLTK dependencies at load-time

    Args:
        lexicon_name (str): name of NLTK lexicon
        logger (:obj:`logging.logger`, optional): logging handle for errors

    Returns:
        (bool): pass/fail

    """
    return download(lexicon_name)

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

class RemoteException(Exception):
    """base exception class for remote modules"""
    pass
class EmptyNewsEndpoint(RemoteException):
    """exception for alerting when news RSS/json returns nothing"""
    pass
class EndpointDown(RemoteException):
    """wrapper for request errors, alert to stop parsing"""
    pass
