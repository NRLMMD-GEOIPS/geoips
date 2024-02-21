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
    def __call__(self, levelName, levelNum, methodName=None):
        """
        Comprehensively adds a new logging level to the `logging` module.

        Comprehensively adds a new logging level to the `logging` module
        and the currently configured logging class.

        `levelName` becomes an attribute of the `logging` module with the value
        `levelNum`. `methodName` becomes a convenience method for both `logging`
        itself and the class returned by `logging.getLoggerClass()` (usually just
        `logging.Logger`). If `methodName` is not specified, `levelName.lower()` is
        used.

        To avoid accidental clobberings of existing attributes, this method will
        raise an `AttributeError` if the level name is already an attribute of the
        `logging` module or if the method name is already present

        Example
        -------
        >>> add_logging_level('TRACE', logging.DEBUG - 5)
        >>> logging.getLogger(__name__).setLevel("TRACE")
        >>> logging.getLogger(__name__).trace('that worked')
        >>> logging.trace('so did this')
        >>> logging.TRACE
        5

        """
        if not methodName:
            methodName = levelName.lower()

        # Add the log level
        if hasattr(logging, levelName):
            if getattr(logging, levelName) != levelNum:
                raise AttributeError(
                    f"{levelName} level already defined in logging module and its value "
                    f"({getattr(logging, levelName)}) differs from the requested value "
                    f"({levelNum})."
                )
        else:
            logging.addLevelName(levelNum, levelName)
            setattr(logging, levelName, levelNum)

        logToRoot = self.get_logToRoot(levelNum)
        if hasattr(logging, methodName):
            if getattr(logging, methodName) != logToRoot:
                raise AttributeError(
                    f"{methodName} method already defined in logging module and differs "
                    f"from the requested method."
                )
        else:
            setattr(logging, methodName, logToRoot)

        loggerClass = logging.getLoggerClass()
        logForLevel = self.get_logForLevel(levelNum)
        if hasattr(loggerClass, methodName):
            if getattr(loggerClass, methodName) != logForLevel:
                raise AttributeError(
                    f"{methodName} method already defined in logger class and differs "
                    f"from the requested method."
                )
        else:
            setattr(loggerClass, methodName, logForLevel)

    def get_logForLevel(self, levelNum):
        if not hasattr(self, "_logForLevel_funcs"):
            self._logForLevel_funcs = {}

        if not levelNum in self._logForLevel_funcs:

            def logForLevel(self, message, *args, **kwargs):
                if self.isEnabledFor(levelNum):
                    self._log(levelNum, message, args, **kwargs)

            self._logForLevel_funcs[levelNum] = logForLevel
        return self._logForLevel_funcs[levelNum]

    def get_logToRoot(self, levelNum):
        if not hasattr(self, "_logToRoot_funcs"):
            self._logToRoot_funcs = {}

        if not levelNum in self._logToRoot_funcs:

            def logToRoot(message, *args, **kwargs):
                logging.log(levelNum, message, *args, **kwargs)

            self._logToRoot_funcs[levelNum] = logToRoot
        return self._logToRoot_funcs[levelNum]


add_logging_level = LogLevelAdder()


def setup_logging(logging_level="INTERACTIVE", verbose=True):
    """Set up logging handler.

    If you do this the first time with no argument, it sets up the logging
    for all submodules. Subsequently, in submodules, you can just do
    LOG = logging.getLogger(__name__)
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
