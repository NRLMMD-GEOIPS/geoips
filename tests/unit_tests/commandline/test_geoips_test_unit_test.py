# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit test for GeoIPS CLI `test unit-test` command.

See geoips/commandline/ancillary_info/cmd_instructions.yaml for more information.
"""

# from glob import glob
# from numpy.random import rand
# from os import listdir
# from os.path import basename
# import pytest
# from importlib.resources import files

# from tests.unit_tests.commandline.cli_top_level_tester import BaseCliTest


# class TestGeoipsTestUnitTest(BaseCliTest):
#     """Unit Testing Class for Test Unit Test Command."""

#     @property
#     def command_combinations(self):
#         """A stochastic list of commands used by the GeoipsTestUnitTest command.

#         This includes failing cases as well.
#         """
#         if not hasattr(self, "_cmd_list"):
#             base_args = ["geoips", "test", "unit-test"]
#             self._cmd_list = [
#                 base_args + ["commandline", "-n", "test_geoips_list_packages.py"]
#             ]
#             # select a small random amount of tests to call via geoips test unit-test
#             for pkg_name in self.plugin_package_names:
#                 unit_test_dir = str(files(pkg_name) / "../tests/unit_tests")
#                 try:
#                     listdir(unit_test_dir)
#                 except FileNotFoundError:
#                     continue
#                 for dir_name in listdir(unit_test_dir):
#                     for test_name in glob(f"{unit_test_dir}/{dir_name}/test*.py"):
#                         test_name = basename(test_name)
#                         do_geoips_test = rand() < 0.05
#                         if do_geoips_test:
#                             self._cmd_list.append(
#                                 base_args + ["-p", pkg_name, dir_name, "-n", test_name] # NOQA
#                             )
#             # Add argument list to retrieve help message
#             self._cmd_list.append(base_args + ["-h"])
#             # Add argument list with non existent package and directory name
#             self._cmd_list.append(
#                 base_args + ["-p", "non_existent_package", "non_existent_dirname"]
#             )
#         return self._cmd_list

#     def check_error(self, args, error):
#         """Ensure that the 'geoips test unit-test ...' error output is correct.

#         Parameters
#         ----------
#         args: 2D list of str
#             - The arguments used to call the CLI (expected to fail)
#         error: str
#             - Multiline str representing the error output of the CLI call
#         """
#         # An error occurred using args. Assert that args is not valid and check the
#         # output of the error.
#         err_str = "To use, type\n`geoips test unit-test -p <package_name> "
#         err_str += "<directory_name> <-n> <script_name>`"
#         assert err_str in error

#     def check_output(self, args, output):
#         """Ensure that the 'geoips unit-test ...' successful output is correct.

#         Parameters
#         ----------
#         args: 2D list of str
#             - The arguments used to call the CLI
#         output: str
#             - Multiline str representing the output of the CLI call
#         """
#         # The args provided are valid, so test that the output is actually correct
#         if "-h" in args:
#             help_str = "To use, type\n`geoips test unit-test -p <package_name> "
#             help_str += "<directory_name> <-n> <script_name>`"
#             assert help_str in output
#         else:
#             # Checking that output from geoips unit-test command reports succeeds
#             assert "test session starts" in output
#             assert "pytest" in output


# test_sub_cmd = TestGeoipsTestUnitTest()


# @pytest.mark.parametrize(
#     "args",
#     test_sub_cmd.command_combinations,
#     ids=test_sub_cmd.generate_id,
# )
# def test_command_combinations(monkeypatch, args):
#     """Test all 'geoips test unit-test ...' commands.

#     This test covers every valid combination of commands for the 'geoips test unit-test' # NOQA
#     command. We also test invalid commands, to ensure that the proper help documentation # NOQA
#     is provided for those using the command incorrectly.

#     Parameters
#     ----------
#     args: 2D array of str
#         - List of arguments to call the CLI with (ie. ['geoips', 'test', 'unit-test'])
#     """
#     test_sub_cmd.test_command_combinations(monkeypatch, args)

# THIS SECTION WAS COMMENTED OUT BECAUSE WE DON"T WANT TO INVOKE PYTEST IN MAIN GEOIPS
# AND THIS COMMAND IS LARGELY FOR EASE OF USE'S SAKE. WE MAY WANT TO USE IT LATER SO
# THAT IS WHY IT HAS NOT BEEN DELETED ALTOGETHER.
