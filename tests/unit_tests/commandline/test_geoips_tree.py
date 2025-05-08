# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit test for GeoIPS CLI `tree` command.

See geoips/commandline/ancillary_info/cmd_instructions.yaml for more information.
"""

# import pytest

# from tests.unit_tests.commandline.cli_top_level_tester import BaseCliTest


# class TestGeoipsTree(BaseCliTest):
#     """Unit Testing Class for Tree Command."""

#     @property
#     def command_combinations(self):
#         """A list of every possible call signature for the GeoipsTree command.

#         This includes failing cases as well.
#         """
#         if not hasattr(self, "_cmd_list"):
#             base_args = ["geoips", "tree"]
#             self._cmd_list = [base_args]
#             for depth in range(1, 4):
#                 self._cmd_list.append(base_args + ["--max-depth", str(depth)])
#                 self._cmd_list.append(
#                     base_args + ["--max-depth", str(depth), "--color"]
#                 )
#                 self._cmd_list.append(
#                     base_args + ["--max-depth", str(depth), "--short-name"]
#                 )
#                 self._cmd_list.append(
#                     base_args + ["--max-depth", str(depth), "--short-name", "--color"]
#                 )
#             self._cmd_list.append(base_args + ["--short-name"])
#             self._cmd_list.append(base_args + ["--color"])
#             self._cmd_list.append(base_args + ["--color", "--short-name"])
#             # Add argument list to retrieve help message
#             self._cmd_list.append(base_args + ["-h"])
#             # Add argument list with invalid depth
#             self._cmd_list.append(base_args + ["--max-depth", "-1"])
#         return self._cmd_list

#     @property
#     def command_tree(self):
#         """A depth-wise mapping of all GeoIPS CLI commands."""
#         if not hasattr(self, "_command_tree"):
#             self._command_tree = {
#                 "geoips": {
#                     "config": ["install"],
#                     "get": ["family", "interface", "package", "plugin"],
#                     "list": [
#                         "interface",
#                         "interfaces",
#                         "packages",
#                         "plugins",
#                         "scripts",
#                         "test-datasets",
#                         "unit-tests",
#                     ],
#                     "run": ["single_source", "data_fusion", "config_based"],
#                     "test": ["linting", "script"],
#                     "tree": [],
#                     "validate": [],
#                 }
#             }
#         return self._command_tree

#     def check_error(self, args, error):
#         """Ensure that the 'geoips tree ...' error output is correct.

#         Parameters
#         ----------
#         args: 2D list of str
#             - The arguments used to call the CLI (expected to fail)
#         error: str
#             - Multiline str representing the error output of the CLI call
#         """
#         # An error occurred using args. Assert that args is not valid and check the
#         # output of the error.
#         err_str = (
#             "To use, type `geoips tree <--max-depth> <int> <--color> <--short-name>`."
#         )
#         assert err_str in error
#         assert args != ["geoips", "tree"]

#     def check_output(self, args, output):
#         """Ensure that the 'geoips tree ...' successful output is correct.

#         Parameters
#         ----------
#         args: 2D list of str
#             - The arguments used to call the CLI
#         output: str
#             - Multiline str representing the output of the CLI call
#         """
#         # Needed as pytest overrides 'geoips' in 'geoips tree' when called
#         # using monkeypatch.
#         output = output.replace("pytest", "geoips")
#         # The args provided are valid, so test that the output is actually correct
#         if "-h" in args or ("--max-depth" in args and "0" in args):
#             usg_str = (
#                 "To use, type `geoips tree <--max-depth> <int> <--color> "
#                 "<--short-name>`."
#             )
#             assert usg_str in output or args == ["geoips", "tree", "--max-depth", "0"]
#         else:
#             # Checking that output from geoips tree command is valid
#             if set(["--max-depth", "1"]) <= set(args):
#                 depth = 1
#             else:
#                 depth = 2

#             short = "--short-name" in args
#             assert "geoips" in output

#             if depth > 0:
#                 for cmd_name in self.command_tree["geoips"]:
#                     if not short:
#                         # full name of command; ie 'geoips list'
#                         assert f"geoips-{cmd_name}" in output
#                     else:
#                         assert cmd_name in output
#                     if depth == 2:
#                         for subcmd_name in self.command_tree["geoips"][cmd_name]:
#                             if not short:
#                                 # full name of command; ie 'geoips list packages'
#                                 assert f"geoips-{cmd_name}-{subcmd_name}" in output
#                             else:
#                                 assert subcmd_name in output


# test_sub_cmd = TestGeoipsTree()


# @pytest.mark.parametrize(
#     "args",
#     test_sub_cmd.command_combinations,
#     ids=test_sub_cmd.generate_id,
# )
# def test_command_combinations(monkeypatch, args):
#     """Test all 'geoips tree ...' commands.

#     This test covers every valid combination of commands for the 'geoips tree'
#     command. We also test invalid commands, to ensure that the proper help documentation  # NOQA
#     is provided for those using the command incorrectly.

#     Parameters
#     ----------
#     args: 2D array of str
#         - List of arguments to call the CLI with (ie. ['geoips', 'tree'])
#     """
#     test_sub_cmd.test_command_combinations(monkeypatch, args)


# NOTE: THIS FILE IS COMMENTED OUT UNTIL THE CLI PRS HAVE BEEN MERGED AND WE CAN MAKE
# ONE FINAL UPDATE THAT WILL ENCAPSULATE ALL NEW FUNCTIONALITY
