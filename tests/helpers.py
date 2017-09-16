"""helpers.py: common utilities for tests"""
from os import path

import prosper.common.prosper_config as p_config

HERE = path.abspath(path.dirname(__file__))
CONFIG_PATH = path.join(HERE, 'test_config.cfg')

CONFIG = p_config.ProsperConfig(CONFIG_PATH)
