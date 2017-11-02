"""test_commands.py: validate core responses for bots"""
from os import path
import platform
import time

from parse import *
import pytest
import tinymongo

import prosper_bots.commands as commands
import prosper_bots.exceptions as exceptions
import prosper_bots._version as version

HERE = path.abspath(path.dirname(__file__))
ROOT = path.abspath(path.join(path.dirname(HERE), 'prosper_bots'))
CACHE_PATH = path.join(HERE, 'cache')


class TestVersionInfo:
    """validate version_info() behavior"""
    app_name = 'TestmodeApp'
    def test_version_info_happypath(self):
        response = commands.version_info(self.app_name)

        values = search('{app_name} -- {version} -- {platform:S}', response)

        assert values['app_name'] == self.app_name
        assert values['version'] == version.__version__
        assert values['platform'] == platform.node()

class TestGenericStockInfo:
    """validate generic_stock_info behavior"""
    stock_ticker = 'MU'
    alternate_ticker = 'INTC'
    conn = tinymongo.TinyMongoClient(CACHE_PATH)['prosper']

    #TODO clear chaces?
    def test_generic_stock_info_happypath(self):
        """make sure expected path works as expected"""
        response = commands.generic_stock_info(
            self.stock_ticker,
            self.conn
        )
        print(response)
        values = search('{company_name} {price:f} {change_pct:%}', response)

        assert values['company_name'] == 'Micron Technology, Inc. - Common Stock'
        assert isinstance(values['price'], float)
        assert isinstance(values['change_pct'], float)

    def test_generic_stock_info_cooldown(self):
        """make sure cooldown works as expected"""
        dump_response = commands.generic_stock_info(
            self.alternate_ticker,
            self.conn,
            cooldown_time=10
        )
        assert dump_response != ''

        response = commands.generic_stock_info(
            self.alternate_ticker,
            self.conn,
            cooldown_time=10
        )
        assert response == ''

        ## TODO: fails multi-thread? ##

    def test_generic_stock_info_badticker(self):
        """validate unsupported ticker response"""
        response = commands.generic_stock_info(
            'BUTTS',
            self.conn
        )
        assert response == ''

class TestGenericCoinInfo:
    """validate generic_stock_info behavior"""
    stock_ticker = 'BTC'
    alternate_ticker = 'ETH'
    conn = tinymongo.TinyMongoClient(CACHE_PATH)['prosper']
    #TODO clear chaces?
    def test_generic_coin_info_happypath(self):
        """make sure expected path works as expected"""
        response = commands.generic_coin_info(
            self.stock_ticker,
            self.conn
        )
        print(response)
        values = search('{coin_name} {price:f} {change_pct:%}', response)

        assert values['coin_name'] == 'Bitcoin'
        assert isinstance(values['price'], float)
        assert isinstance(values['change_pct'], float)

    def test_generic_coin_info_cooldown(self):
        """make sure cooldown works as expected"""
        dump_response = commands.generic_coin_info(
            self.alternate_ticker,
            self.conn,
            cooldown_time=10
        )
        assert dump_response != ''

        response = commands.generic_coin_info(
            self.alternate_ticker,
            self.conn,
            cooldown_time=10
        )

        assert response == ''

    def test_generic_coin_info_badticker(self):
        """validate unsupported ticker response"""
        response = commands.generic_coin_info(
            'BUTTS',
            self.conn
        )
        assert response == ''


class TestStockNews:
    """validate stock_news behavior"""
    stock_ticker = 'MU'
    alt_ticker = 'INTC'
    bad_ticker = 'BUTTS'

    def retry_stock_news(self, direction):
        """retry with a different ticker"""
        return commands.stock_news(
            self.alt_ticker,
            direction
        )
    def test_stock_news_happypath_pos(self):
        """make sure service works as expected - positive case"""
        url, score = commands.stock_news(
            self.stock_ticker,
            1.0
        )
        if not url:
            url, score = self.retry_stock_news(1.0)

        assert isinstance(url, str)
        assert isinstance(score, str)  # scores are cast to str

        assert float(score) >= 0.0

    def test_stock_news_happypath_neg(self):
        """make sure service works as expected - negative case"""
        url, score = commands.stock_news(
            self.stock_ticker,
            -1.0
        )
        if not url:
            url, score = self.retry_stock_news(1.0)

        assert isinstance(url, str)
        assert isinstance(score, str)  # scores are cast to str

        assert float(score) <= 0.0

    def test_stock_news_happypath_neut(self):
        """make sure service works as expected - neutral case"""
        url, score = commands.stock_news(
            self.stock_ticker,
            0.0
        )

        assert url == ''
        assert score == ''

    def test_stock_news_badticker(self):
        """invalid ticker behavior"""
        url, score = commands.stock_news(
            self.bad_ticker,
            1.0
        )

        assert 'ERROR - ' in url
        assert score == ''
