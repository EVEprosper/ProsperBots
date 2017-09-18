"""test_commands.py: validate core responses for bots"""
from os import path
import platform

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
    conn = tinymongo.TinyMongoClient(CACHE_PATH)['prosper']
    #TODO clear chaces?
    def test_generic_stock_info_happypath(self):
        """make sure expected path works as expected"""
        response = commands.generic_stock_info(
            self.stock_ticker,
            self.conn
        )
        values = search('{company_name} {price:f} {change_pct:%}', response)

        assert values['company_name'] == 'Micron Technology, Inc. - Common Stock'
        assert isinstance(values['price'], float)
        assert isinstance(values['change_pct'], float)

    def test_generic_stock_info_cooldown(self):
        """make sure cooldown works as expected"""
        response = commands.generic_stock_info(
            self.stock_ticker,
            self.conn,
            cooldown_time=10
        )

        assert response == ''

    def test_generic_stock_info_badticker(self):
        """validate unsupported ticker response"""
        response = commands.generic_stock_info(
            'BUTTS',
            self.conn
        )
        assert response == ''
