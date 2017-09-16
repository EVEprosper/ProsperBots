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

def test_clear_cache():
    """destroy any remaining cache files"""
    try:
        shutil.rmtree(CACHE_PATH)
    except Exception:
        pytest.xfail('No cache to clear: {}'.format(CACHE_PATH))

def test_build_connection():
    """validate happy-path behavior for build_connection"""
    dummy_conn = connections.build_connection(
        'test_source',
        source_path=CACHE_PATH
    )

    assert isinstance(dummy_conn, tinymongo.tinymongo.TinyMongoDatabase)

    assert path.isfile(path.join(CACHE_PATH, 'test_source.json'))
