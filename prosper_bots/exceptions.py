"""exceptions.py: custom exceptions for bots"""
class ProsperBotException(Exception):
    """base class for ProsperBots exceptions"""
    pass

class ConnectionsException(ProsperBotException):
    """class for prosper_bots.connections"""
    pass
class TooManyOptions(ConnectionsException):
    """bot is confused, can't pick the right option out of many"""
    pass
class EmptyQuoteReturned(ProsperBotException):
    """expected quote data, got back nothing.  Don't go forward"""
    pass
