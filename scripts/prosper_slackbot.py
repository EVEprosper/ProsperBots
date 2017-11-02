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
import prosper_bots.slack_utils as slack_utils
import prosper_bots.commands as commands

HERE = path.abspath(path.dirname(__file__))
CONFIG = p_config.ProsperConfig(path.join(HERE, 'bot_config.cfg'))
PROGNAME = 'ProsperSlackBot'
CONN = connections.build_connection('slackbot')
PP = pprint.PrettyPrinter(indent=2)

@slackbot.bot.respond_to('version', re.IGNORECASE)
def which_prosperbot(message):
    """echo deployment info"""
    message_info = slack_utils.parse_message_metadata(message)
    api_config.LOGGER.info(
        '#%s @%s -- Version Info',
        message_info['channel_name'],
        message_info['user_name']
    )
    try:
        version_str = commands.version_info(PROGNAME)
    except Exception:  # pragma: no cover
        api_config.LOGGER.error('Unable to build version info', exc_info=True)

    message.send(version_str)


@slackbot.bot.respond_to('set mode (.*)')
def change_mode(message, mode):
    """set expected mode for channel"""
    message_info = slack_utils.parse_message_metadata(message)
    print(message._body)
    api_config.LOGGER.info(
        '#%s @%s -- Setting channel mode %s',
        message_info['channel_name'],
        message_info['user_name'],
        mode
    )

    try:
        set_mode = connections.set_channel_mode(
            message_info['channel'],
            mode,
            message_info['user_name'],
            CONN,
            logger=api_config.LOGGER
        )
    except Exception as err:
        api_config.LOGGER.error(
            'Unable to set #%s to %s',
            message_info['channel_name'],
            mode,
            exc_info=True
        )
        message.send('Unable to set mode {} for channel: `{}`'.format(mode, repr(err)))
        return

    message.send('OK, I set this channel to `{}`'.format(set_mode.value))


@slackbot.bot.listen_to(r'`\$(.*)`')
def generic_stock_info(message, ticker):
    """echo basic info about stock"""
    ticker = ticker.upper()
    message_info = slack_utils.parse_message_metadata(message)
    api_config.LOGGER.info(
        '#%s @%s -- Basic company info %s',
        message_info['channel_name'],
        message_info['user_name'],
        ticker
    )

    mode = connections.check_channel_mode(
        message_info['channel'],
        CONN,
        logger=api_config.LOGGER
    )
    api_config.LOGGER.info('Channel mode: %s', mode.value)
    try:
        if mode == connections.Modes.stocks:
            data = commands.generic_stock_info(
                ticker,
                CONN,
                cooldown_time=CONFIG.get_option('ProsperBot', 'generic_info', None, 30),
                logger=api_config.LOGGER
            )
        elif mode == connections.Modes.coins:
            data = commands.generic_coin_info(
                ticker,
                CONN,
                cooldown_time=CONFIG.get_option('ProsperBot', 'generic_info', None, 30),
                logger=api_config.LOGGER
            )
        else:
            api_config.LOGGER.error(
                'UNEXPECTED CHANNEL MODE -- #%s %s',
                message_info['channel_name'],
                str(mode),
                exc_info=True
            )
            data = ''
    except Exception:  # pramga: no cover
        api_config.LOGGER.error('Unable to resolve basic stock info for %s', ticker, exc_info=True)
        data = ''

    if data:  # only emit if there is data
        api_config.LOGGER.debug(data)
        message.send('`' + data + '`')

@slackbot.bot.listen_to(r'^news \$*(.*)', re.IGNORECASE)
def stock_news(message, ticker):
    """fetch relevant article for requested stock"""
    ticker = ticker.upper()
    message_info = slack_utils.parse_message_metadata(message)
    api_config.LOGGER.info(
        '#%s @%s -- Stock News %s',
        message_info['channel_name'],
        message_info['user_name'],
        ticker
    )

    mode = connections.check_channel_mode(
        message_info['channel'],
        CONN,
        logger=api_config.LOGGER
    )
    api_config.LOGGER.info('Channel mode: %s', mode.value)
    try:
        if mode == connections.Modes.stocks:
            quote = commands.generic_stock_info(
                ticker, CONN, cooldown_time=0, logger=api_config.LOGGER,
                info_mask=['name', 'current_price', 'change_pct']
            )
            direction = float(quote.split()[-1].replace('%', ''))
            link, details = commands.stock_news(
                ticker,
                direction,
                logger=api_config.LOGGER
            )

        elif mode == connections.Modes.coins:
            api_config.LOGGER.warning('not supported')
            message.send('mode=coins not supported')
            quote=''
        else:
            api_config.LOGGER.error(
                'UNEXPECTED CHANNEL MODE -- #%s %s',
                message_info['channel_name'],
                str(mode),
                exc_info=True
            )
            quote = ''
    except Exception:
        api_config.LOGGER.error(
            'Unable to resolve basic stock info for %s',
            ticker, exc_info=True
        )
        quote = ''

    if quote:  # only emit if there is data
        api_config.LOGGER.debug(quote)
        message.send(
            '`' + quote + '`' +
            link #+ ' ' + details
        )

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
        try:
            bot = slackbot.bot.Bot()
            bot.run()
        except Exception:
            logger.critical('Going down in flames!', exc_info=True)

if __name__ == '__main__':
    ProsperSlackBot.run()
