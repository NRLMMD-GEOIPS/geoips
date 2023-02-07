class EntryPointError(Exception):
    """Exception to be raised when an entry-point cannot be found."""

    pass


class PluginError(Exception):
    """Exception to be raised when there is an error in a plugin module."""

    pass
