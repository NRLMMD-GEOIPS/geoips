# # # Distribution Statement A. Approved for public release. Distribution unlimited.
# # #
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # #
# # # This program is free software: you can redistribute it and/or modify it under
# # # the terms of the NRLMMD License included with this program. This program is
# # # distributed WITHOUT ANY WARRANTY; without even the implied warranty of
# # # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the included license
# # # for more details. If you did not receive the license, for more information see:
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/

"""Geoips module for setting up logging handlers with a specified verbosity."""

import logging
import sys


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


def setup_logging(logging_level="INTERACTIVE", verbose=True):
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
    logging_level : str, default="INTERACTIVE"
        Sets the minimum log level for which log output will be written to stdout.
    verbose : bool, default=True
        Determines which log formatter will be used. If `True`, a longer format will be
        used, providing more information, but also cluttering the screen. If `False`, a
        shorter format will be used.
    """
    log = logging.getLogger()
    log.setLevel(getattr(logging, logging_level))
    fmt = logging.Formatter(
        "%(asctime)s %(module)12s.py:%(lineno)-4d %(levelname)7s: %(message)s",
        "%d_%H%M%S",
    )
    if not verbose:
        fmt = logging.Formatter("%(asctime)s: %(message)s", "%d_%H%M%S")
    stream_hndlr = logging.StreamHandler(sys.stdout)
    stream_hndlr.setFormatter(fmt)
    stream_hndlr.setLevel(logging.INFO)
    log.addHandler(stream_hndlr)
    return log
