"""prosper_slackbot.py: main method for slackbot"""
from os import path

import slackbot
from plumbum import cli

import prosper_bots
import prosper.common.prosper_logging as p_logging
import prosper.common.prosper_config as p_config

HERE = path.abspath(path.dirname(__file__))
CONFIG = p_config.ProsperConfig(path.join(HERE, 'bot_config.cfg'))


class ProsperSlackBot(cli.Application):
    """wrapper for slackbot Main()"""
    PROGNAME = 'ProsperSlackBot'
    VERSION = prosper_bots._version.__version__

    _log_builder = p_logging.ProsperLogger(
        PROGNAME,
        '/var/logs/prosper',
        config=CONFIG
    )

    debug = cli.Flag(
        ['d', '--debug'],
        help='debug mode, high verbosity for devs'
    )

    def main(self):
        """bot main"""
        if self.debug:
            self._log_builder.configure_debug_logger()
        else:
            self._log_builder.configure_slack_logger()

        logger = self._log_builder.logger

        logger.info('Hello World')

if __name__ == '__main__':
    ProsperSlackBot.run()
