"""GeoIPS CLI "test" command.

Runs the appropriate tests based on the arguments provided.
"""

from glob import glob
from importlib import resources
from os.path import basename
from subprocess import call

from geoips.commandline.geoips_command import GeoipsCommand, GeoipsExecutableCommand


class GeoipsTestUnitTest(GeoipsExecutableCommand):
    """GeoipsTest Sub-Command for running GeoIPS Tests."""

    subcommand_name = "unit-test"
    subcommand_classes = []

    def add_arguments(self):
        """Add arguments to the test-subparser for the Test Command."""
        pass

    def __call__(self, args):
        """Run the provided unit tests based on the arguments provided."""
        pass


class GeoipsTestScript(GeoipsExecutableCommand):
    """GeoipsTest Sub-Command for running GeoIPS Tests."""

    subcommand_name = "script"
    subcommand_classes = []

    def add_arguments(self):
        """Instantiate the arguments that are supported for the test script command.

        Currently the "geoips test script" command supports this format:
            - geoips test script <package_name> <script_name> -i
        Where:
            - <package_name> is any GeoIPS package that is installed and recognized by
              the GeoIPS Library
            - <script_name> is the name of the bash script being tested
            - '-i' represents whether or not this script is an 'integration' test
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
            "-i",
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
        call(script_path, shell=True)


class GeoipsTestLinting(GeoipsExecutableCommand):
    """GeoipsTest Sub-Command for running GeoIPS Tests."""

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
            call(f"{lint_path} {linter} {package_path}", shell=True)


class GeoipsTest(GeoipsCommand):
    """GeoipsTest Sub-Command for running GeoIPS Tests."""

    subcommand_name = "test"
    subcommand_classes = [GeoipsTestLinting, GeoipsTestScript, GeoipsTestUnitTest]
