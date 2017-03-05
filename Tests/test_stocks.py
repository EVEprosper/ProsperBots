"""test_stocks.py

Pytest functions for exercising prosper.stocks packages

"""
from os import path
import pytest

import prosper.stocks.remote as p_remote

HERE = path.abspath(path.dirname(__file__))
ROOT = path.dirname(HERE)

def test_news_happypath():
    """test p_remote.get_news endpoint for happy-path"""
    test_ticker_list = [
        'A',
        'FB',
        'WF',
        'USO'
    ]
    for test_ticker in test_ticker_list:
        data = p_remote.get_news(test_ticker)

    ##TODO test data has sections##

def test_news_badaddr():
    """test p_remote.get_news endpoint for downtime"""
    test_ticker = 'WF'
    with pytest.raises(p_remote.EndpointDown):
        data = p_remote.get_news(
            test_ticker,
            news_uri='http://api.eveprosper.com/noendpoint'
        )

def test_news_emptyval():
    """test p_remote.get_news endpoint for blank feed"""
    test_ticker = 'ABRN'
    with pytest.raises(p_remote.EmptyNewsEndpoint):
        data = p_remote.get_news(test_ticker)
