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

        # The requested level (e.g. GeoIPS' custom "interactive" level) may not be
        # registered yet during early package imports. Fall back to ``info`` so a
        # missing optional dependency never turns into an AttributeError -- this
        # previously broke ``import geoips`` (and therefore autodoc/doc builds) in
        # environments that did not have every optional dependency installed.
        log_method = getattr(LOG, loglevel, None)
        if not callable(log_method):
            log_method = LOG.info
        log_method(err_str)
