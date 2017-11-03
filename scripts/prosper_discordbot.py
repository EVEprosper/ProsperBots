"""prosper_discordbot.py: main method for slackbot"""
from os import path
import platform
import re
import pprint

import discord
from discord.ext import commands as discord_commands
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
import prosper_bots.platform_utils as platform_utils
import prosper_bots.commands as commands
import prosper_bots.exceptions as exceptions

HERE = path.abspath(path.dirname(__file__))
CONFIG = p_config.ProsperConfig(path.join(HERE, 'bot_config.cfg'))
PROGNAME = 'ProsperDiscordBot'
CONN = connections.build_connection('discordbot')
PP = pprint.PrettyPrinter(indent=2)

bot = discord_commands.Bot(
    command_prefix=CONFIG.get('DiscordBot', 'bot_prefix'),
    description='ProsperBot is BESTBOT'
)

@bot.event
async def on_ready():
    api_config.LOGGER.info('Logged in as')
    api_config.LOGGER.info(bot.user.name)
    api_config.LOGGER.info(bot.user.id)
    api_config.LOGGER.info('------')

@bot.command(pass_context=True)
async def version(context):
    """echo deployment info"""
    message_info = platform_utils.parse_discord_context_object(context)
    api_config.LOGGER.info(
        '%s #%s @%s -- Version Info',
        message_info['team_name'],
        message_info['channel_name'],
        message_info['user_name'],
    )

    try:
        version_str = commands.version_info(PROGNAME)
    except Exception:  # pragma: no cover
        api_config.LOGGER.error('Unable to build version info', exc_info=True)

    await bot.say(version_str)

@bot.command(pass_context=True)
async def price(context, ticker):
    """fetch relevant article for requested stock"""
    ticker = ticker.upper()
    message_info = platform_utils.parse_discord_context_object(context)
    api_config.LOGGER.info(
        '%s #%s @%s -- Stock News',
        message_info['team_name'],
        message_info['channel_name'],
        message_info['user_name'],
    )

    try:
        quote = commands.generic_stock_info(
            ticker, CONN, cooldown_time=0, logger=api_config.LOGGER,
            info_mask=['name', 'current_price', 'change_pct']
        )
        if not quote:
            raise exceptions.EmptyQuoteReturned

        direction = float(quote.split()[-1].replace('%', ''))
        link, details = commands.stock_news(
            ticker,
            direction,
            logger=api_config.LOGGER
        )
    except exceptions.ProsperBotException:
        api_config.LOGGER.warning(
            'Unable to resolve basic stock info for %s',
            ticker, exc_info=True
        )
        quote = 'ERROR - NO QUOTE DATA FOUND FOR {}'.format(ticker)
        link = ''
        details = ''
    except Exception as err:
        api_config.LOGGER.error(
            'Unable to resolve basic stock info for %s',
            ticker, exc_info=True
        )
        quote = 'ERROR - UNABLE TO RESOLVE NEWS {} -- {}'.format(
            ticker,
            repr(err)
        )
        link = ''

    if quote:  # only emit if there is data
        api_config.LOGGER.debug(quote)
        await bot.say(
            '```' + quote + '```\n' +
            link + ' ' + details
        )

class ProsperDiscordBot(cli.Application):
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
            self._log_builder.configure_discord_logger()

        logger = self._log_builder.logger

        logger.info('Hello World')
        api_config.LOGGER = logger
        api_config.CONFIG = CONFIG

        logger.error('STARTING PROSPERBOT -- DISCORD %s', platform.node())
        try:
            status = bot.run(CONFIG.get('DiscordBot', 'api_token'))
        except Exception:
            logger.critical('Going down in flames!', exc_info=True)

        logger.warning('Discord.py exited unexpectedly: {}'.format(status))

if __name__ == '__main__':
    ProsperDiscordBot.run()
