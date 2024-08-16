# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Module for handling optional dependencies throughout GeoIPS."""

from contextlib import contextmanager
import logging
import os
import sys
import traceback

LOG = logging.getLogger(__name__)


@contextmanager
def import_optional_dependencies(loglevel="info"):
    """Attempt to import a package and log the event if the import fails.

    Parameters
    ----------
    loglevel : str
        Name of the log level to write to. May be any valid log level (e.g. debug, info,
        etc.).
    """
    try:
        yield None
    except ImportError as err:
        tb = traceback.extract_tb(err.__traceback__)
        filename, lineno, _, _ = tb[-1]
        err_str = f"Failed to import {err.name} at {filename}:{lineno}. "
        err_str += "If you need it, install it."

        getattr(LOG, loglevel)(err_str)


@contextmanager
def suppress_output():
    """Suppress the output going to the terminal for case-specific situations.

    This is used by the CLI to suppress warnings from 3rd Party packages that are not
    relevant to the CLI and confuscate important output.

    Use this for any case in which you are running a function[s], but don't want its
    output to be sent to the terminal.
    """
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = devnull
        sys.stderr = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
