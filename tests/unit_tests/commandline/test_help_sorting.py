# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit test for GeoIPS CLI help messages."""

import argparse

from geoips.commandline.geoips_command import AlphabeticalHelpFormatter


class TestAlphabeticalHelpFormatter:
    """
    :noindex: Test suite for AlphabeticalHelpFormatter.

    Ensures that the custom help formatter correctly sorts
    command-line arguments in alphabetical order.

    Tests cover:
    - Mixed argument types (options and positional arguments)
    - Arguments with multiple aliases
    - Complex option string configurations
    """

    def test_sorting_with_mixed_arguments(self):
        """
        Test sorting of arguments with mixed types and flags.

        Verifies alphabetical sorting of:
        - Options with short and long flags
        - Positional arguments
        - Arguments with multiple aliases
        """
        parser = argparse.ArgumentParser(formatter_class=AlphabeticalHelpFormatter)

        # Add arguments in non-alphabetical order with various types
        parser.add_argument("-z", "--zeta", help="Zeta option")
        parser.add_argument("gamma", help="Gamma positional argument")
        parser.add_argument("-a", "--alpha", help="Alpha option")
        parser.add_argument("beta", help="Beta positional argument")
        parser.add_argument("-m", "--middle", help="Middle option")

        # Capture help output
        help_output = parser.format_help()
        help_output = help_output[help_output.index("\n") :]  # skip first line

        # Verify alphabetical ordering
        assert help_output.index("--alpha") < help_output.index("--middle")
        assert help_output.index("--middle") < help_output.index("--zeta")
        assert help_output.index("beta") < help_output.index("gamma")

    def test_sorting_with_complex_option_strings(self):
        """
        Test sorting of arguments with multiple option strings and aliases.

        Ensures alphabetical ordering based on first option string.
        """
        parser = argparse.ArgumentParser(formatter_class=AlphabeticalHelpFormatter)

        # Add arguments with multiple option strings and aliases
        parser.add_argument("-z", "--zeta", "--zebra", help="Zeta option")
        parser.add_argument("-a", "--alpha", "--apple", help="Alpha option")
        parser.add_argument("-m", "--middle", "--monkey", help="Middle option")

        # Capture help output
        help_output = parser.format_help()
        help_output = help_output[help_output.index("\n") :]  # skip first line

        # Verify alphabetical ordering based on first option string
        assert help_output.index("--alpha") < help_output.index("--middle")
        assert help_output.index("--middle") < help_output.index("--zeta")

    def test_sorting_with_no_option_strings(self):
        """
        Test sorting of arguments without option strings.

        Verifies alphabetical ordering of positional arguments.
        """
        parser = argparse.ArgumentParser(formatter_class=AlphabeticalHelpFormatter)

        # Add positional arguments
        parser.add_argument("zeta", help="Zeta argument")
        parser.add_argument("alpha", help="Alpha argument")
        parser.add_argument("middle", help="Middle argument")

        # Capture help output
        help_output = parser.format_help()
        help_output = help_output[help_output.index("\n") :]  # skip first line

        # Verify alphabetical ordering
        assert help_output.index("alpha") < help_output.index("middle")
        assert help_output.index("middle") < help_output.index("zeta")
