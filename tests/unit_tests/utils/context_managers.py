# # # Distribution Statement A. Approved for public release. Distribution is unlimited.
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

"""Unit Tests for log output for optional dependencies found throughout geoips."""

import logging
import pytest
from geoips.utils import context_managers

opt_importer = context_managers.import_optional_dependencies
importer_path = context_managers.__file__

LOG = logging.getLogger(__name__)

# err_str = f"Failed to import {err.name} at {filename}:{lineno}. "
# err_str += "If you need it, install it."


@pytest.mark.parametrize("loglevel", ["info", "debug", "warning", "error"])
def test_import_failure_using_log(loglevel, caplog):
    """Ensure that the test fails and that the log output is correct."""
    caplog.set_level(getattr(logging, loglevel.upper()))
    with opt_importer(loglevel=loglevel):
        """Attempt to import a package and print to LOG.info if the import fails."""
        import non_existent_package  # noqa

    err_str = f"Failed to import non_existent_package at {importer_path}:24. "
    err_str += "If you need it, install it."

    assert err_str in caplog.text


@pytest.mark.parametrize("loglevel", ["info", "debug", "warning", "error"])
def test_import_success_using_log(loglevel, caplog):
    """Ensure that the test succeeds and that the log output is empty."""
    caplog.set_level(getattr(logging, loglevel.upper()))
    with opt_importer(loglevel=loglevel):
        """Attempt to import a package and print to LOG.info if the import fails."""
        import numpy  # noqa

    assert caplog.text == ""
