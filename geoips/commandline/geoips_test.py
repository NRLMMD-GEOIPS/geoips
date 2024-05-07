"""GeoIPS CLI "test" command.

Runs the appropriate tests based on the arguments provided.
"""

from glob import glob
from importlib import resources
# from os import listdir
from os.path import basename
# from pytest import main as invoke_pytest
from subprocess import call

from geoips.commandline.geoips_command import GeoipsCommand, GeoipsExecutableCommand


# class GeoipsTestUnitTest(GeoipsExecutableCommand):
#     """Test Sub-Command for running GeoIPS Unit Tests."""

#     subcommand_name = "unit-test"
#     subcommand_classes = []

#     def add_arguments(self):
#         """Instantiate the arguments that are supported for the test unit-test command.

#         Currently the "geoips test unit-test" command supports this format:
#             - geoips test unit-test dir_name <-p> <package_name> <-n> <test_name>
#         Where:
#             - dir_name is the name of the folder containing the unit-test[s] you want to
#               run
#             - <package_name> is any GeoIPS package that is installed and recognized by
#               the GeoIPS Library
#             - <test_name> is the name of the unit test being ran
#         """
#         self.subcommand_parser.add_argument(
#             "directory_name",
#             type=str,
#             help="GeoIPS Packages Unit Test Directory Name where unit tests are held.",
#         )
#         self.subcommand_parser.add_argument(
#             "--package_name",
#             "-p",
#             type=str,
#             default="geoips",
#             choices=self.plugin_packages,
#             help="GeoIPS Package containing the unit-tests to be ran.",
#         )
#         self.subcommand_parser.add_argument(
#             "--name_of_test",
#             "-n",
#             type=str,
#             default=None,
#             help="Specific Unit Test to be ran out of directory_name.",
#         )

#     def __call__(self, args):
#         """Run the provided unit tests based on the arguments provided."""
#         dir_name = args.directory_name
#         package_name = args.package_name
#         test_name = args.name_of_test
#         unit_test_dir = str(resources.files(package_name) / "../tests/unit_tests")

#         try:
#             # Try listing the expected unit test directory. If it fails, raise an
#             # argparse error which states such package doesn't have a unit tests
#             # directory
#             listdir(unit_test_dir)
#         except FileNotFoundError:
#             err_str = f"No unit tests directory found for package '{package_name}'."
#             self.subcommand_parser.error(err_str)

#         if dir_name not in listdir(unit_test_dir):
#             # The specified unit test directory does not exist at the specified location
#             # raise an error specifying that
#             err_str = f"Directory '{dir_name}' not found under {package_name}'s unit "
#             err_str += f"tests directory '{unit_test_dir}'. Please select one of the "
#             err_str += f"following unit test directories:\n {listdir(unit_test_dir)}"
#             self.subcommand_parser.error(err_str)
#         elif test_name is not None:
#             # We've specified a specific Unit Test to run out of
#             # <package_name>/tests/unit_tests/<dir_name>/<script_name>, ensure that
#             # file actually exists
#             fnames = [
#                 basename(fpath)
#                 for fpath in glob(f"{unit_test_dir}/{dir_name}/test_*.py")
#             ]
#             if test_name not in fnames:
#                 err_str = f"Unit Test '{test_name}' not found under the directory "
#                 err_str += f"'{unit_test_dir}', please select one of the options shown "
#                 err_str += f"below.\ns {fnames}"
#                 self.subcommand_parser.error(err_str)
#         else:
#             # script name wasn't specified, run all unit tests found under
#             # <package_name>/tests/unit_tests/<dir_name>
#             test_name = "."

#         test_path = str(f"{unit_test_dir}/{dir_name}/{test_name}")
#         invoke_pytest(["-v", test_path])


class GeoipsTestScript(GeoipsExecutableCommand):
    """Test Sub-Command for running GeoIPS Test Scripts."""

    subcommand_name = "script"
    subcommand_classes = []

    def add_arguments(self):
        """Instantiate the arguments that are supported for the test script command.

        Currently the "geoips test script" command supports this format:
            - geoips test script <-p> <package_name> <script_name> <--integration>
        Where:
            - <package_name> is any GeoIPS package that is installed and recognized by
              the GeoIPS Library
            - <script_name> is the name of the bash script being tested
            - '--integration' represents whether or not this is an 'integration' test
        """
        self.subcommand_parser.add_argument(
            "script_name",
            type=str,
            help="GeoIPS Script to be tested",
        )
        self.subcommand_parser.add_argument(
            "--package_name",
            "-p",
            type=str,
            default="geoips",
            choices=self.plugin_packages,
            help="GeoIPS Package containing the script to be tested",
        )
        self.subcommand_parser.add_argument(
            "--integration",
            default=False,
            action="store_true",
            help="Whether or not the script is an integration test.",
        )

    def __call__(self, args):
        """Run the provided test script based off the arguments provided.

        This will run the provided test script, locating such script based on whether
        or not this was an integration-based test. If it wasn't, we'll look through the
        corresponding <package_name>/tests/scripts/ directory for the correct test
        script.

        Parameters
        ----------
        args: Argparse Namespace()
            - The list argument namespace to parse through
        """
        package_name = args.package_name
        script_name = args.script_name
        is_integration_test = args.integration

        if is_integration_test:
            if package_name != "geoips":
                # Raise an argparse error which states only geoips supports integration
                # testing
                err_str = "Only package 'geoips' has integration tests. Package "
                err_str += f"'{package_name}' doesn't have those tests. Try again."
                self.subcommand_parser.error(err_str)
            dir_name = "integration_tests"
        else:
            dir_name = "scripts"

        test_dir = str(resources.files(package_name) / f"../tests/{dir_name}")
        fnames = [basename(fpath) for fpath in glob(f"{test_dir}/*.sh")]

        if script_name not in fnames:
            # Raise an argparse error which states that file doesn't exist within the
            # specified directory
            str_fnames = ",\n".join(fnames)
            err_str = f"Script '{script_name}' doesn't exist within '{test_dir}/'. "
            err_str += "Please select a valid script from this directory listing:\n"
            err_str += str_fnames
            self.subcommand_parser.error(err_str)

        script_path = f"{test_dir}/{script_name}"
        # Run the corresponding test
        call(["bash", script_path], shell=False)


class GeoipsTestLinting(GeoipsExecutableCommand):
    """Test Sub-Command for running GeoIPS Linting Services."""

    subcommand_name = "linting"
    subcommand_classes = []

    def add_arguments(self):
        """Add arguments to the test-subparser for the Test Linting Command."""
        self.subcommand_parser.add_argument(
            "--package_name",
            "-p",
            type=str,
            default="geoips",
            choices=self.plugin_packages,
            help="GeoIPS Package that we want to run linting tests on.",
        )

    def __call__(self, args):
        """Run all GeoIPS Linting Tests on the provided package."""
        package_name = args.package_name
        lint_path = str(resources.files("geoips") / "../tests/utils/check_code.sh")
        package_path = str(resources.files(package_name) / "../.")
        for linter in ["bandit", "black", "flake8"]:
            call(["bash", lint_path, linter, package_path], shell=False)


class GeoipsTest(GeoipsCommand):
    """Top-Level Test Command for testing GeoIPS and its corresponding Packages."""

    subcommand_name = "test"
    subcommand_classes = [GeoipsTestLinting, GeoipsTestScript]
    # subcommand_classes = [GeoipsTestLinting, GeoipsTestScript, GeoipsTestUnitTest]
