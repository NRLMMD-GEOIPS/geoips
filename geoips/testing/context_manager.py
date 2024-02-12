"""Module for handling optional dependencies throughout GeoIPS."""


import logging
from contextlib import contextmanager

LOG = logging.getLogger(__name__)


@contextmanager
def import_optional_dependences(importer):
    """Attempt to import a package and print to LOG.info if the import fails."""
    try:
        yield None
    except ImportError as err:
        err_str = f"Failed to import {err.name} in {importer}. "
        err_str += "If you need it, install it."
        LOG.info(err_str)
