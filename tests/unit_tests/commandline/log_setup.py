"""Test log.interative from GeoIPS."""

import pytest

import os
from glob import glob


def test_log_interactive_non_geoips():
    """Ensure that log.interactive fails for standard logging module.

    This is to ensure that GeoIPS doesn't pollute the logging module.
    """
    import logging

    log = logging.getLogger(__name__)
    with pytest.raises(AttributeError):
        log.interactive("FROM PYTEST")


def test_log_interactive_geoips(caplog):
    """Test log.interactive using logging from geoips."""
    from geoips.__init__ import logging as gi_logging

    log = gi_logging.getLogger(__name__)

    log.interactive("FROM PYTEST")
    assert "FROM PYTEST" in caplog.text
    assert "INTERACTIVE" in caplog.text


def test_log_interactive_from_directly_imported_plugin(caplog):
    """Use ABI reader, which calls log.interactive.

    It used to be that plugins loaded via get_plugin outside of GeoIPS could not call
    log.interactive. They would raise an AttributeError. This is to ensure that problem
    has been fixed and remains fixed.
    """
    from geoips.interfaces import readers

    reader = readers.get_plugin("abi_netcdf")

    test_data_dir = os.getenv("GEOIPS_TESTDATA_DIR")
    test_data_dir += "/test_data_noaa_aws/data/goes16/20200918/1950"
    test_data_files = glob(test_data_dir + "/*C14*.nc")
    _ = reader(test_data_files)
    assert "INTERACTIVE" in caplog.text
