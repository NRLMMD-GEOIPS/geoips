# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Test all Output Checker plugins."""

import pytest

from geoips.interfaces import output_checkers
from geoips.commandline import log_setup

log_setup.setup_logging()

# If this is set to a path, this path will be used for storing the test data files
# Otherwise a tmp_path directory will be used and deleted at the end of each test
# For more information see here: https://docs.pytest.org/en/7.1.x/how-to/tmp_path.html
permanent_test_data_dir = None


class TestOutputCheckers:
    """TestOutputChecker class, defining methods as well."""

    from geoips.interfaces import output_checkers

    available_output_checkers = [
        str(checker.name) for checker in output_checkers.get_plugins()
    ]

    def compare_plugin(self, tmp_path, plugin):
        """Test the comparision of two products with the appropriate Output Checker."""
        if permanent_test_data_dir:
            compare_paths, output_paths = plugin.module.get_test_files(
                permanent_test_data_dir
            )
        else:
            compare_paths, output_paths = plugin.module.get_test_files(tmp_path)
        plugin.module.perform_test_comparisons(plugin, compare_paths, output_paths)

    @pytest.mark.parametrize("checker_name", available_output_checkers)
    def test_plugins(self, tmp_path, checker_name):
        """Test all output_checkers that are ready for testing."""
        plugin = output_checkers.get_plugin(checker_name)
        # Note "long" running output checkers unit tests are not currently
        # supported.  For now, xfail if we come across a "long" unit test.
        # We will eventually implement "long" running unit tests, but for
        # not just xfail.
        if hasattr(plugin.module, "get_test_files_long") or not hasattr(
            plugin.module, "perform_test_comparisons_long"
        ):
            pytest.xfail(checker_name + " should be run with the long unit tests.")
        if not hasattr(plugin.module, "get_test_files") or not hasattr(
            plugin.module, "perform_test_comparisons"
        ):
            pytest.xfail(checker_name + " is not ready to be tested yet.")
        self.compare_plugin(tmp_path, plugin)
