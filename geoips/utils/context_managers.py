"""Module for handling optional dependencies throughout GeoIPS."""

import logging
from contextlib import contextmanager
import sys

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
        filename = sys.exc_info()[2].tb_frame.f_code.co_filename
        lineno = sys.exc_info()[2].tb_frame.f_lineno
        err_str = f"Failed to import {err.name} at {filename}:{lineno}. "
        err_str += "If you need it, install it."

        getattr(LOG, loglevel)(err_str)
        # print(err_str)
