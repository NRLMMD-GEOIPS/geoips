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
from geoips.geoips_utils import get_entry_point_group

log_setup.setup_logging()


class TestOutputCheckers:
    """TestOutputChecker class, defining methods as well."""

    from os.path import basename, exists
    from os import listdir
    from importlib.resources import files

    plugin_packages = get_entry_point_group("geoips.plugin_packages")
    available_output_checkers = []
    for pkg in plugin_packages:
        dir_path = str(files(pkg.value) / "plugins/modules/output_checkers") + "/"
        if exists(dir_path):
            for output_checker_path in listdir(dir_path):
                if "__pycache__" not in output_checker_path:
                    # get the basename of the path and remove the .py extension
                    available_output_checkers.append(
                        str(basename(output_checker_path))[:-3]
                    )

    def compare_plugin(self, plugin):
        """Test the comparision of two products with the appropriate Output Checker."""
        compare_paths, output_paths = plugin.module.get_test_files()
        plugin.module.perform_test_comparisons(plugin, compare_paths, output_paths)

    @pytest.mark.parametrize("checker_name", available_output_checkers)
    def test_plugins(self, checker_name):
        """Test all output_checkers that are ready for testing."""
        plugin = output_checkers.get_plugin(checker_name)
        if not hasattr(plugin.module, "get_test_files") or not hasattr(
            plugin.module, "perform_test_comparisons"
        ):
            pytest.xfail(checker_name + " is not ready to be tested yet.")
        self.compare_plugin(plugin)
