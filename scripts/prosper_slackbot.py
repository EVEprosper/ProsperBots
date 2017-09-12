"""prosper_slackbot.py: main method for slackbot"""
from os import path
import platform
import re
import pprint
import json

import slackbot.bot
from plumbum import cli
from contexttimer import Timer
import requests

import prosper.common.prosper_logging as p_logging
import prosper.common.prosper_config as p_config

## TODO: need more path than expected?
from prosper_bots._version import __version__
import prosper_bots.config as api_config
import prosper_bots.utils as utils
import prosper_bots.connections as connections

HERE = path.abspath(path.dirname(__file__))
CONFIG = p_config.ProsperConfig(path.join(HERE, 'bot_config.cfg'))
PROGNAME = 'ProsperSlackBot'
PP = pprint.PrettyPrinter(indent=2)

@slackbot.bot.respond_to('version', re.IGNORECASE)
def which_prosperbot(message):
    """echo deployment info"""
    api_config.LOGGER.info(
        '@%s -- Version Info -- %s',
        message._client.users[message._body['user']]['name'],
        __version__
    )
    message.send('{} -- {} -- {}'.format(
        PROGNAME,
        __version__,
        platform.node()
    ))

@slackbot.bot.listen_to(r'`\$(.*)`')
def generic_stock_info(message, ticker):
    """echo basic info about stock"""
    ticker = ticker.upper()
    api_config.LOGGER.info(
        '@%s -- Basic company info -- %s',
        message._client.users[message._body['user']]['name'],
        ticker
    )
    if connections.cooldown(
            'BASIC-{}'.format(ticker),
            cooldown_time=CONFIG.get_option('ProsperBot', 'generic_info', None, 30),
            logger=api_config.LOGGER
    ):
        api_config.LOGGER.info('--CALLED TOO QUICKLY: shutting up')
        return

    with Timer() as basic_quote_timer:
        try:
            data = utils.get_basic_ticker_info(
                ticker.upper(),
                ['company_name', 'last', 'change_pct'],
                logger=api_config.LOGGER
            )
        except Exception:
            api_config.LOGGER.error(
                'Unexpected get_basic_ticker_info() failure',
                exc_info=True
            )
            data = ''
        api_config.LOGGER.info('--basic_quote_timer=%s', basic_quote_timer)

    if data:  # only emit if there is data
        api_config.LOGGER.debug(data)
        message.send('`' + data + '`')

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
