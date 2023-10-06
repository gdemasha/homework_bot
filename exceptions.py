class UnexpectedStatusCodeException(Exception):
    """A custom exception for an unexpected status code."""

    pass


class NoEnvVarException(Exception):
    """A custom exception for missing environmental variables."""

    pass


class SendMessageException(Exception):
    """A custom exception for a failure of sending a message."""

    pass


class ChatIDIsDigitException(Exception):
    """A custom exception for checking if chat ID is a digit."""

    pass
