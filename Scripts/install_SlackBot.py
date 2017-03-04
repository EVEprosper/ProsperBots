#!/usr/bin/env python3

"""Install utility for setting up SlackBot

NOTE: designed to run on default python with minimal dependencies

"""

from os import path
import logging
import pip

try:
    from plumbum import cli, local
except ImportError:
    pip.main(['install', 'plumbum'])
    from plumbum import cli, local

#try:
#    import prosper.common.prosper_logging
#except ImportError:
#    pip_command = local['pip']
#    pip_command(
#        'install',
#        'ProsperCommon~=0.4.0',
#        '--extra-index-url=https://repo.fury.io/lockefox/'
#    )
#    import prosper.common.prosper_logging as p_logging
#    import prosper.common.prosper_config as p_config

HERE = path.abspath(path.dirname(__file__))
ROOT = path.dirname(HERE)
CONFIG_PATH = path.join(HERE, 'installer_config.cfg')

DEFAULT_LOGGER = logging.getLogger('NULL')
DEFAULT_LOGGER.addHandler(logging.NullHandler())

LOGGER = DEFAULT_LOGGER

def build_default_logger(log_level='INFO'):
    """set up defaults for logging

    Args:
        log_level (str): minimum logging level enum

    Returns:
        (:obj:`logging.logger`) default logger
    """
    log_path = path.join(HERE, 'installer.log')
    logger = logging.getLogger('SlackBot_installer')
    formatter = logging.Formatter(
        '[%(asctime)s;%(levelname)s;%(filename)s;%(funcName)s;%(lineno)s] %(message)s'
    )
    handler = logging.FileHandler(log_path)

    handler.setFormatter(formatter)
    handler.setLevel(log_level)
    logger.addHandler(handler)

    return logger


class SlackInstaller(cli.Application):
    """Installer for Prosper's SlackBot"""
    _logger = build_default_logger()
    debug = cli.Flag(
        ['-d', '--debug'],
        help='Toggle debug mode: do not actually install services'
    )

    @cli.switch(
        ['-v', '--verbose'],
        help='Enable verbose messaging')
    def enable_verbose(self):
        """toggle verbose logger"""
        debug_handler = logging.StreamHandler()
        debug_formatter = logging.Formatter(
            '[%(levelname)s:%(filename)s--%(funcName)s:%(lineno)s] %(message)s'
        )
        debug_handler.setFormatter(debug_formatter)
        debug_handler.setLevel('DEBUG')
        self._logger.addHandler(debug_handler)

    webhook_url = None
    @cli.switch(
        ['-w', '--webhook'],
        str,
        help='Webhook URL for logging errors to slack')
    def set_webhook(self, webhook_url):
        """set webhook url"""
        self.webhook_url = webhook_url

    bot_token = None
    @cli.switch(
        ['-t', '--token'],
        str,
        help='bot token authentication')
    def set_bottoken(self, bot_token):
        """set bot id"""
        self.bot_token = bot_token

    config_override = None
    @cli.switch(
        ['-c', '--config'],
        str,
        help='custom .cfg file to override bot .cfg file (DOES NOT AFFECT INSTALLER CONFIG)'
    )
    def set_config_override(self, config_override_path):
        """override the generic included config with a custom version"""
        pass

    def main(self):
        """script logic goes here"""
        global LOGGER
        LOGGER = self._logger

if __name__ == '__main__':
    SlackInstaller.run()
