# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Geoips module for setting up logging handlers with a specified verbosity."""

import logging
import sys
from textwrap import wrap
from os import getenv
from socket import gethostname

from geoips.filenames.base_paths import PATHS as gpaths


logging.captureWarnings(True)


def log_with_emphasis(print_func, *messages):
    """Print messages boxed in asterisks using the specified print function.

    Print one or more messages using the specified print function. The messages
    will be surrounded in asterisks. Long messages will be word wrapped to fit
    within a maximum width of 74 characters, save for any individual words that
    are over 74 characters which will not be broken.

    Parameters
    ----------
    print_func: func
        An instance of a function that prints (e.g. ``logging.debug``, ``logging.info``,
        etc, or the ``print`` function itself).
    messages: one or more strings
        The messages to be logged with emphasis
    """
    wrapped_messages = []
    # Even though only strings should be passed here, we are going to allow any type of
    # object to be passed for the time being. Best not to overthink the situation and
    # just cast for the time being.
    messages = filter(lambda s: len(str(s)) > 0, messages)

    for message in messages:
        # wrap the message to a specified length
        wrapped_messages += wrap(
            message, width=74, break_long_words=False, break_on_hyphens=False
        )
    try:
        max_message_len = min(74, max([len(wmessage) for wmessage in wrapped_messages]))
    except ValueError as e:
        raise ValueError(
            "No proper messages were provided for logging.\n"
            + "Make sure the messages are not all empty strings."
        ) from e
    # adding +6 to max_message_len as we add '** ' and ' **' pre/post-fixes (6 chars)
    print_func("*" * (max_message_len + 6))
    for wrapped_message in wrapped_messages:
        # for each of the wrapped messages, if the length of such message is less
        # than max message length, add some whitespace to make some things match,
        # this is what the 'ljust(len)' function does
        print_func(f"** {wrapped_message.ljust(max_message_len)} **")
    print_func("*" * (max_message_len + 6))
    print_func("\n")


class LogLevelAdder:
    """Create a callable that can add a new logging level.

    Initialize simply as `add_log_level = LogLevelAdder()` and add a new level by
    calling `add_log_level` with the name of the new log level and its level number.

    For further call information, see the docstring for LogLevelAdder.__call__().
    """

    def __call__(self, level_name, level_num):
        """Comprehensively adds a new logging level to the `logging` module.

        Comprehensively adds a new logging level named `level_name` to the `logging`
        module and the currently configured logging class. The new logging level's
        precidence is set by `level_num`. For example, a level_num of `15` would create
        a logging level that falls between `logging.DEBUG` and `logging.INFO` whose
        level_num are `10` and `20`, respectively.

        Calling this function will add the following to the logging class:
        - A new log level named `logging.{level_name}`
        - A new logging function called `logging.{level_name.lower()]}`

        To avoid conflicts between the log level attribute and the logging function,
        `level_name` must not be entirely lowercase.

        Parameters
        ----------
        level_name : str
            Name for the new log level. This must not be completely lowercase.
        level_num : int
            Numeric precidence of the new log level.

        `level_name` becomes an attribute of the `logging` module with the value
        `level_num`. `methodName` becomes a convenience method for both `logging`
        itself and the class returned by `logging.getLoggerClass()` (usually just
        `logging.Logger`). If `methodName` is not specified, `level_name.lower()` is
        used.

        To avoid accidental clobberings of existing attributes, this method will
        raise an `AttributeError` if the level name is already an attribute of the
        `logging` module or if the method name is already present

        Example
        -------
        >>> add_logging_level = LogLevelAdder()
        >>> add_logging_level('TRACE', logging.DEBUG - 5)
        >>> logging.getLogger(__name__).setLevel("TRACE")
        >>> logging.getLogger(__name__).trace('that worked')
        >>> logging.trace('so did this')
        >>> logging.TRACE
        5

        """
        methodName = level_name.lower()

        # Add the log level
        if hasattr(logging, level_name):
            if getattr(logging, level_name) != level_num:
                raise AttributeError(
                    f"{level_name} level already defined in logging module and its "
                    f"value ({getattr(logging, level_name)}) differs from the "
                    f"requested value ({level_num})."
                )
        else:
            logging.addLevelName(level_num, level_name)
            setattr(logging, level_name, level_num)

        # Add the logging method to the current root logger
        logToRoot = self._get_logToRoot(level_num)
        if hasattr(logging, methodName):
            if getattr(logging, methodName) != logToRoot:
                raise AttributeError(
                    f"{methodName} method already defined in logging module and "
                    f"differs from the requested method."
                )
        else:
            setattr(logging, methodName, logToRoot)

        # Add the logging method to the logger class so it gets attached to new logger
        # instances moving forward
        loggerClass = logging.getLoggerClass()
        logForLevel = self._get_logForLevel(level_num)
        if hasattr(loggerClass, methodName):
            if getattr(loggerClass, methodName) != logForLevel:
                raise AttributeError(
                    f"{methodName} method already defined in logger class and differs "
                    f"from the requested method."
                )
        else:
            setattr(loggerClass, methodName, logForLevel)

    def _get_logForLevel(self, level_num):
        if not hasattr(self, "_logForLevel_funcs"):
            self._logForLevel_funcs = {}

        if level_num not in self._logForLevel_funcs:

            def logForLevel(self, message, *args, **kwargs):
                if self.isEnabledFor(level_num):
                    self._log(level_num, message, args, **kwargs)

            self._logForLevel_funcs[level_num] = logForLevel
        return self._logForLevel_funcs[level_num]

    def _get_logToRoot(self, level_num):
        if not hasattr(self, "_logToRoot_funcs"):
            self._logToRoot_funcs = {}

        if level_num not in self._logToRoot_funcs:

            def logToRoot(message, *args, **kwargs):
                logging.log(level_num, message, *args, **kwargs)

            self._logToRoot_funcs[level_num] = logToRoot
        return self._logToRoot_funcs[level_num]


add_logging_level = LogLevelAdder()


def setup_logging(logging_level=None, fmt_string=None, datefmt_string=None):
    """Get a new logger instance for GeoIPS.

    Get a new logger instance for GeoIPS. This will set the logger's logging level, its
    formatter, and add a `StreamHandler` pointing to `sys.stdout`.

    This is most often used at the top-level of an applcation to set up the root logger
    for the application (e.g. in a command line script). Once configured, the root
    logger's properties will be inherited by lower-level logger instances. So, to use
    the same logging configuration in submodules, simply instantiate a new logger
    instance via `LOG = logging.getLogger(__name__)` and it will behave the same as the
    root logger.

    Parameters
    ----------
    logging_level : str, default=None
        Sets the minimum log level for which log output will be written to stdout.
        If None, will default to value set in base_paths.  This allows using
        GEOIPS_LOGGING_LEVEL to override default.
    fmt_string: str, default=None
        Explicitly specify the log formatter format string. If None, default
        to the value set in geoips/filenames/base_paths (which in the future
        will be replaced with a GeoIPS config file).
    datefmt_string: str, default=None
        Explicitly specify the log formatter datefmt string. If None, default
        to the value set in geoips/filenames/base_paths (which in the future
        will be replaced with a GeoIPS config file).
    """
    log = logging.getLogger()

    ###########################################################################
    # Identify the current requested logging level

    # If logging_level was not specified, default to base_path specification here.
    if not logging_level:
        logging_level = gpaths["GEOIPS_LOGGING_LEVEL"]
    log.setLevel(getattr(logging, logging_level.upper()))

    ###########################################################################
    # Identify the current requested format and date format strings for
    # log formatter.

    if fmt_string is None:
        # Note that any format specifications supported directly by the
        # logging.Formatter fmt keyword argument are specified as %(fmtspec)
        # Username and hostname were not directly supported by logging.Formatter,
        # so we added the capability to include them via os.getenv and
        # socket.gethostname and f-string formatting.
        fmt_string = gpaths["GEOIPS_LOGGING_FMT_STRING"]
    if datefmt_string is None:
        datefmt_string = gpaths["GEOIPS_LOGGING_DATEFMT_STRING"]

    ###########################################################################
    # Now replace any variables specified as {varname} within the format string.

    username = getenv("USER")
    hostname = gethostname()

    # These are the variables explicitly supported in the format string, no other
    # variables specified with {varname} are supported.
    fmt_vars = {"username": username, "hostname": hostname}
    # Identify which of the above variables are actually in the format string.
    fmt_kwargs = {x: y for x, y in fmt_vars.items() if x in fmt_string}
    # Pass each of the variables specified in the format string as keyword
    # arguments to the format method of the string.  Ie,
    # fmt_string.format(username=username, hostname=hostname)
    fmt_string = fmt_string.format(**fmt_kwargs)

    ###########################################################################
    # Set the actual log formatter using fmt_string and datefmt_string.

    fmt = logging.Formatter(fmt=fmt_string, datefmt=datefmt_string)

    ###########################################################################
    # Set the log handlers if they are not already set

    if not log.handlers:
        stream_hndlr = logging.StreamHandler(sys.stdout)
        stream_hndlr.setFormatter(fmt)
        stream_hndlr.setLevel(logging.INFO)
        log.addHandler(stream_hndlr)

    ###########################################################################
    # Print username and host at the info level at the beginning of the log output

    log.info(f"USER: {username}")
    log.info(f"HOST: {hostname}")

    ###########################################################################
    # Return the resulting log for use throughout GeoIPS

    return log
