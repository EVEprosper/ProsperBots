"""slack_utils.py: slack-specific utilities"""
from os import path

HERE = path.abspath(path.dirname(__file__))

def parse_message_metadata(message_obj):
    """parse user_name/channel_name out of slack controller

    Notes:
        `slackbot.message`.keys(): [type, channel, user, text, ts, source_team, team]
    Args:
        message_obj (:obj:`slackbot.message`): response object for slack

    Returns:
        (:obj:`dict`): message data

    """
    metadata = dict(message_obj._body)
    try:
        metadata['channel_name'] = message_obj._client.channels[metadata['channel']]['name']
    except KeyError:
        metadata['channel_name'] = '__DIRECT_MESSAGE'
    metadata['user_name'] = message_obj._client.users[metadata['user']]['name']
    metadata['team_name'] = message_obj._client.login_data['team']['name']

    return metadata
