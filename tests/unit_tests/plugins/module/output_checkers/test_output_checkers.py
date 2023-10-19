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

"""Test all Output Checker plugins."""
import pytest

from geoips.interfaces import output_checkers
from geoips.commandline import log_setup

log_setup.setup_logging()


class TestOutputCheckers:
    """TestOutputChecker class, defining methods as well."""

    available_output_checkers = ["geotiff", "image", "netcdf", "text"]

    def compare_plugin(self, plugin):
        """Test the comparision of two products with the appropriate Output Checker."""
        compare_paths, output_paths = plugin.module.yield_test_files()
        plugin.module.perform_test_comparisons(plugin, compare_paths, output_paths)

    @pytest.mark.parametrize("checker_name", available_output_checkers)
    def test_plugins(self, checker_name):
        """Test all output_checkers that are ready for testing."""
        plugin = output_checkers.get_plugin(checker_name)
        if not hasattr(plugin.module, "yield_test_files") or not hasattr(
            plugin.module, "perform_test_comparisons"
        ):
            pytest.xfail(checker_name + " is not ready to be tested yet.")
        self.compare_plugin(plugin)
