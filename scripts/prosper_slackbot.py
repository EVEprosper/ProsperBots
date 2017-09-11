"""prosper_slackbot.py: main method for slackbot"""
from os import path
import platform
import re
import pprint

import slackbot.bot
from plumbum import cli

import prosper.common.prosper_logging as p_logging
import prosper.common.prosper_config as p_config

## TODO: need more path than expected?
from prosper_bots._version import __version__
import prosper_bots.config as api_config

HERE = path.abspath(path.dirname(__file__))
CONFIG = p_config.ProsperConfig(path.join(HERE, 'bot_config.cfg'))
PROGNAME = 'ProsperSlackBot'
PP = pprint.PrettyPrinter(indent=2)

@slackbot.bot.respond_to('VERSION')
def which_prosperbot(message):
    """echo deployment info"""
    message.send('{} -- {} -- {}'.format(
        PROGNAME,
        __version__,
        platform.node()
    ))

@slackbot.bot.listen_to(r'`\$(.*)`')
def generic_stock_info(message, ticker):
    """echo basic info about stock"""

    PP.pprint(message._body)
    api_config.LOGGER.info(
        'Basic company info -- %s -- @%s',
        ticker.upper(),
        message._client.users[message._body['user']]['name'])
    message.send(ticker)

class ProsperSlackBot(cli.Application):
    """wrapper for slackbot Main()"""
    PROGNAME = PROGNAME
    VERSION = __version__

    _log_builder = p_logging.ProsperLogger(
        PROGNAME,
        '/var/logs/prosper',
        config_obj=CONFIG
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
        api_config.LOGGER = logger
        api_config.CONFIG = CONFIG

        logger.error('STARTING PROSPERBOT -- SLACK %s', platform.node())
        bot = slackbot.bot.Bot()
        bot.run()

if __name__ == '__main__':
    ProsperSlackBot.run()
