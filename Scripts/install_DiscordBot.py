#!/usr/bin/env python3

"""Install utility for setting up DiscordBot"""

from os import path
import pip

try:
    from plumbum import cli, local
except ImportError:
    pip.main(['install', 'plumbum'])
    from plumbum import cli, local

try:
    import prosper.common.prosper_logging
except ImportError:
    pip_command = local['pip']
    pip_command(
        'install',
        'ProsperCommon~=0.4.0',
        '--extra-index-url=https://repo.fury.io/lockefox/'
    )
    import prosper.common.prosper_logging as p_logging
    import prosper.common.prosper_config as p_config

HERE = path.abspath(path.dirname(__file__))
ROOT = path.dirname(HERE)
CONFIG_PATH = path.join(HERE, 'installer_config.cfg')

CONFIG = p_config.ProsperConfig(CONFIG_PATH)
LOGGER = p_logging.DEFAULT_LOGGER

class DiscordInstaller(cli.Application):
    """Installer for Prosper's DiscordBot"""
    _log_builder = p_logging.ProsperLogging(
        'DiscordInstaller',
        HERE,
        config_obj=CONFIG
    )
    debug = cli.Flag(
        ['-d', '--debug'],
        help='Toggle debug mode: do not actually install services'
    )

    @cli.switch(
        ['-v', '--verbose'],
        help='Enable verbose messaging')
    def enable_verbose(self):
        """toggle verbose logger"""
        self._log_builder.configure_debug_logger()

    webhook_url = None
    @cli.switch(
        ['-w', '--webhook'],
        str,
        help='Webhook URL for logging errors to discord')
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
        help='Generic .cfg file to override bot .cfg file'
    )
    def set_config_override(self, config_override_path):
        """override the generic included config with a custom version"""
        pass

    def main(self):
        """script logic goes here"""
        global LOGGER
        LOGGER = self._log_builder.get_logger()

if __name__ == '__main__':
    DiscordInstaller.run()
