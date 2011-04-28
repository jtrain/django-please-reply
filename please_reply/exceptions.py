class PleaseReplyException(Exception):
    """Base exception for please reply application."""

class NotInvited(PleaseReplyException):
    """Guest tried to reply to an event they were not invited to."""

class InvalidHash(PleaseReplyException):
    """Invalid key to decrypt hash."""
