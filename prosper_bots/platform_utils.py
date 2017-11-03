"""slack_utils.py: slack-specific utilities"""
from os import path
import pprint

HERE = path.abspath(path.dirname(__file__))
PP = pprint.PrettyPrinter(indent=2)

def parse_slack_message_object(message_obj):
    """parse user_name/channel_name out of slack controller

    Notes:
        `slackbot.message`.keys(): [type, channel, user, text, ts, source_team, team]

    Args:
        message_obj (:obj:`slackbot.message`): response object for slack

    Returns:
        dict: message data

    """
    metadata = dict(message_obj._body)
    try:
        metadata['channel_name'] = message_obj._client.channels[metadata['channel']]['name']
    except KeyError:
        metadata['channel_name'] = 'DIRECT_MESSAGE:{}'.format(
            message_obj._client.users[metadata['user']]['name']
        )
    metadata['user_name'] = message_obj._client.users[metadata['user']]['name']
    metadata['team_name'] = message_obj._client.login_data['team']['name']

    return metadata

def parse_discord_context_object(context_obj):
    """parse user_name/channel_name out of discord controller

    Args:
        context_obj (:obj:`discord.context`): response object for discord

    Returns:
        dict: standardized message data

    """
    metadata = dict()  # TODO: all context_obj.message.{children}.name values
    metadata['user_name'] = context_obj.message.author.name
    metadata['team_name'] = context_obj.message.server.name
    try:
        metadata['channel_name'] = context_obj.message.channel.name
    except Exception:
        metadata['channel_name'] = 'DIRECT_MESSAGE:{}'.format(context_obj.message.author.name)

    return metadata
