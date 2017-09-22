"""test_connections.py: validate behavior for connections"""
from datetime import datetime
from os import path
import shutil

import pytest
import helpers
import tinymongo

import prosper_bots.connections as connections
import prosper_bots.exceptions as exceptions

HERE = path.abspath(path.dirname(__file__))
ROOT = path.abspath(path.join(path.dirname(HERE), 'prosper_bots'))
CACHE_PATH = path.join(HERE, 'cache')

def test_build_connection():
    """validate happy-path behavior for build_connection"""
    dummy_conn = connections.build_connection(
        'test_source',
        source_path=CACHE_PATH
    )

    assert isinstance(dummy_conn, tinymongo.tinymongo.TinyMongoDatabase)

    assert path.isfile(path.join(CACHE_PATH, 'test_source.json'))

class TestChannelMode:
    """validate behavior for set_channel_mode & check_channel_mode"""
    conn = tinymongo.TinyMongoClient(CACHE_PATH)['prosper']

    def test_check_channel_mode_default(self):
        """validate happy-path behavior for set_channel_mode"""
        default_mode = connections.check_channel_mode(
            'DEFAULT_CHANNEL',
            self.conn
        )

        assert isinstance(default_mode, connections.Modes)

        assert default_mode == connections.DEFAULT_MODE

    def test_check_channel_mode_bad_enum(self):
        """validate enums validate as expected"""
        test_channel = 'bad_enum'

        self.conn[connections.CHANNEL_COLLECTION].insert_one({
            'channel_name': test_channel,
            'channel_mode': 'butts',
            'channel_set_time': 'datetime-not-checked',
            'user_name': 'DummyUser'
        })
        with pytest.raises(ValueError):
            channel_mode = connections.check_channel_mode(
                test_channel,
                self.conn
            )

    def test_check_channel_mode_too_much(self):
        """validate exception if too many configs found"""
        test_channel = 'check_too_much_config'

        self.conn[connections.CHANNEL_COLLECTION].insert_one({
            'channel_name': test_channel,
            'channel_mode': 'test',
            'channel_set_time': 'datetime-not-checked',
            'user_name': 'DummyUser'
        })
        self.conn[connections.CHANNEL_COLLECTION].insert_one({
            'channel_name': test_channel,
            'channel_mode': 'test',
            'channel_set_time': 'datetime-not-checked',
            'user_name': 'DummyUser'
        })
        with pytest.raises(exceptions.TooManyOptions):
            channel_mode = connections.check_channel_mode(
                test_channel,
                self.conn
            )

    def test_set_and_check_loop(self):
        """validate setting/reading channel info works as expected"""
        test_channel = 'SET_AND_CHECK'
        set_mode = connections.set_channel_mode(
            test_channel,
            'TEST',
            'DummyUser',
            self.conn
        )
        ## check expected outcome ##
        assert isinstance(set_mode, connections.Modes)
        assert set_mode == connections.Modes.test

        check_mode = connections.check_channel_mode(
            test_channel,
            self.conn
        )
        assert isinstance(check_mode, connections.Modes)
        assert set_mode == connections.Modes.test

    def test_set_channel_too_much(self):
        """validate exception if too many configs found"""
        test_channel = 'set_too_much_config'

        self.conn[connections.CHANNEL_COLLECTION].insert_one({
            'channel_name': test_channel,
            'channel_mode': 'test',
            'channel_set_time': 'datetime-not-checked',
            'user_name': 'DummyUser'
        })
        self.conn[connections.CHANNEL_COLLECTION].insert_one({
            'channel_name': test_channel,
            'channel_mode': 'test',
            'channel_set_time': 'datetime-not-checked',
            'user_name': 'DummyUser'
        })
        with pytest.raises(exceptions.TooManyOptions):
            channel_mode = connections.set_channel_mode(
                test_channel,
                'TEST',
                'DummyUser',
                self.conn
            )
