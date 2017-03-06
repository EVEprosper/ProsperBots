"""test_stocks.py

Pytest functions for exercising prosper.stocks packages

"""
from os import path, remove, makedirs
from datetime import datetime, timedelta
import configparser

import pytest
from tinydb import TinyDB

import prosper.stocks.remote as p_remote
#import prosper.common.prosper_config as p_config

HERE = path.abspath(path.dirname(__file__))
ROOT = path.dirname(HERE)

def get_config(config_path):
    """parse config object for test information

    Args:
        config_path (str): path to config file (abspath > relpath)

    Returns:
        (:obj:`configparser.ConfigParser`) config object

    """
    #TODO: add stupid-parsing to common.prosper_config

    local_config_path = config_path.replace('.cfg', '_local.cfg')
    real_config_path = ''
    if path.isfile(local_config_path):
        real_config_path = local_config_path
    else:
        real_config_path = config_path

    config = configparser.ConfigParser(
        interpolation=configparser.ExtendedInterpolation(),
        allow_no_value=True,
        delimiters=('='),
        inline_comment_prefixes=('#')
    )

    with open(real_config_path, 'r') as handle:
        config.read_file(handle)

    return config

CONFIG = get_config(path.join(HERE, 'test_stocks.cfg'))
CACHE_PATH = path.join(HERE, 'cache')
makedirs(CACHE_PATH, exist_ok=True)
#def test_cleanup_testdir():
#    """make sure paths are cleaned up"""
#    for path_info in CONFIG.items('CACHE'):
#        try:
#            nuke_path = path.join(CACHE_PATH, path_info[1])
#            remove(nuke_path)
#        except Exception:
#            #don't fail, just try to clean up paths
#            pass

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

def overwrite_calendar_status(
        calendar_obj,
        new_value
):
    """force 'status' to some other value"""
    new_calendar = {}
    new_calendar['calendar'] = {}
    new_calendar['calendar']['days'] = {}
    new_calendar['calendar']['days']['day'] = []
    for date_row in calendar_obj['calendar']['days']['day']:
        date_row['status'] = new_value
        new_calendar['calendar']['days']['day'].append(date_row)

    return new_calendar

def close_and_reopen_cache(
        tinydb_cache,
        path_to_cache
):
    """force the tinydb cache closed and reopen it"""
    tinydb_cache.close()
    remove(path_to_cache)
    new_db = TinyDB(path_to_cache)
    return new_db

CALENDAR_CACHE_FILE = path.join(CACHE_PATH, CONFIG.get('CACHE', 'calendar_cache'))
CALENDAR_CACHE = TinyDB(CALENDAR_CACHE_FILE)

@pytest.mark.incremental
class TestTradierTools:
    """wrapper for Tradier functions to test in a block

    Most rely on previous steps to complete correctly
    """
    def test_clear_cache(self):
        """cleanup cache before testing"""
        global CALENDAR_CACHE
        CALENDAR_CACHE = close_and_reopen_cache(
            CALENDAR_CACHE,
            CALENDAR_CACHE_FILE
        )

    def test_tradier_happypath(self):
        """test regular path for tradier calendar utility"""
        if len(CONFIG.get('AUTH', 'tradier_api')) == 0:
            pytest.xfail('missing AUTH for Tradier API')
        status = p_remote.market_open(
            CONFIG.get('AUTH', 'tradier_api'),
            cache_buster=False,
            calendar_cache=CALENDAR_CACHE
        )

    def test_tradier_cachepath(self):
        """make sure cache-only fetch works"""
        status = p_remote.market_open(
            CONFIG.get('AUTH', 'tradier_api'),
            cache_buster=True,
            calendar_cache=CALENDAR_CACHE
        )

    def test_validate_market_open_status(self):
        """make sure cache/remote agree"""
        remote_status = p_remote.market_open(
            CONFIG.get('AUTH', 'tradier_api'),
            cache_buster=True
        )

        cache_value = p_remote.check_calendar_cache(
            CALENDAR_CACHE
        )

        cache_status = None
        if cache_value == p_remote.MarketStatus.OPEN:
            cache_staus = True
        else:
            cache_status = False

        assert cache_status == remote_status

    def test_fail_tradier_fetch(self):
        """force fetch_tradier_calendar to fail"""
        with pytest.raises(Exception):
            p_remote.fetch_tradier_calendar(
                CONFIG.get('AUTH', 'tradier_api'),
                endpoint_url='http://api.eveprosper.com/noendpoint'
            )

    def test_fail_calendar_parse(self):
        """try to validate a bad config"""
        ## Find out-of-range day
        today = datetime.today()
        today_str = today.strftime('%Y-%m-%d')
        next_month = today + timedelta(days=31)
        next_month_str = next_month.strftime('%Y-%m-%d')

        ## Make a calendar with bad values
        good_calendar = p_remote.fetch_tradier_calendar(
            CONFIG.get('AUTH', 'tradier_api')
        )
        bad_calendar = overwrite_calendar_status(
            good_calendar,
            'GARBAGE'
        )

        with pytest.raises(p_remote.UnexpectedMarketStatus):
            status = p_remote.parse_tradier_calendar(
                bad_calendar,
                today_str
            )
            #assert status == p_remote.MarketStatus.UNKNOWN

        with pytest.raises(p_remote.UnexpectedMarketStatus):
            status = p_remote.parse_tradier_calendar(
                good_calendar,
                next_month_str
            )
            #assert status == p_remote.MarketStatus.UNKNOWN

    def test_force_open_calendar(self):
        """make sure we test "OPEN" path"""
        today = datetime.today()
        today_str = today.strftime('%Y-%m-%d')
        good_calendar = p_remote.fetch_tradier_calendar(
            CONFIG.get('AUTH', 'tradier_api')
        )
        open_calendar = overwrite_calendar_status(
            good_calendar,
            'open'
        )

        status = p_remote.parse_tradier_calendar(
            open_calendar,
            today_str
        )
        assert status == p_remote.MarketStatus.OPEN

    def test_force_closed_calendar(self):
        """make sure we test "CLOSED" path"""
        today = datetime.today()
        today_str = today.strftime('%Y-%m-%d')
        good_calendar = p_remote.fetch_tradier_calendar(
            CONFIG.get('AUTH', 'tradier_api')
        )
        closed_calendar = overwrite_calendar_status(
            good_calendar,
            'closed'
        )

        status = p_remote.parse_tradier_calendar(
            closed_calendar,
            today_str
        )
        assert status == p_remote.MarketStatus.CLOSED

    def test_force_bad_cache(self):
        """force bad cache into archive"""
        global CALENDAR_CACHE
        CALENDAR_CACHE = close_and_reopen_cache(
            CALENDAR_CACHE,
            CALENDAR_CACHE_FILE
        )

        good_calendar = p_remote.fetch_tradier_calendar(
            CONFIG.get('AUTH', 'tradier_api')
        )
        bad_calendar = overwrite_calendar_status(
            good_calendar,
            'GARBAGE'
        )

        p_remote.update_calendar_cache(
            CALENDAR_CACHE,
            bad_calendar
        )

        with pytest.raises(p_remote.UnexpectedMarketStatus):
            status = p_remote.check_calendar_cache(CALENDAR_CACHE)
            print(status)

    def test_force_open_cache(self):
        """force cache to "OPEN" status"""
        global CALENDAR_CACHE
        CALENDAR_CACHE = close_and_reopen_cache(
            CALENDAR_CACHE,
            CALENDAR_CACHE_FILE
        )

        good_calendar = p_remote.fetch_tradier_calendar(
            CONFIG.get('AUTH', 'tradier_api')
        )
        open_calendar = overwrite_calendar_status(
            good_calendar,
            'open'
        )

        p_remote.update_calendar_cache(
            CALENDAR_CACHE,
            open_calendar
        )

        status = p_remote.check_calendar_cache(CALENDAR_CACHE)

        assert status == p_remote.MarketStatus.OPEN

    def test_force_closed_cache(self):
        """force cache to "CLOSED" status"""
        global CALENDAR_CACHE
        CALENDAR_CACHE = close_and_reopen_cache(
            CALENDAR_CACHE,
            CALENDAR_CACHE_FILE
        )

        good_calendar = p_remote.fetch_tradier_calendar(
            CONFIG.get('AUTH', 'tradier_api')
        )
        closed_calendar = overwrite_calendar_status(
            good_calendar,
            'closed'
        )

        p_remote.update_calendar_cache(
            CALENDAR_CACHE,
            closed_calendar
        )

        status = p_remote.check_calendar_cache(CALENDAR_CACHE)

        assert status == p_remote.MarketStatus.CLOSED
