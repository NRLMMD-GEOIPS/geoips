# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Module for handling optional dependencies throughout GeoIPS."""

import logging
from contextlib import contextmanager
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
        # print(err_str)
