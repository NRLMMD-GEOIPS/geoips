# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""GeoIPS CLI "test" command.

Runs the appropriate tests based on the arguments provided.
"""

from glob import glob
from importlib import resources
import warnings

# from os import listdir
from os import makedirs
from os.path import basename, exists, join
from geoips.filenames.base_paths import PATHS
import sys

# from pytest import main as invoke_pytest
from subprocess import call

from geoips.commandline.geoips_command import GeoipsCommand, GeoipsExecutableCommand
from geoips.errors import PluginError
from geoips.geoips_utils import is_editable
from geoips.interfaces import sectors


# class GeoipsTestUnitTest(GeoipsExecutableCommand):
#     """Test Command for running GeoIPS Unit Tests."""

#     name = "unit-test"
#     command_classes = []

#     def add_arguments(self):
#         """Instantiate the arguments that are supported for the test unit-test command. # NOQA

#         Currently the "geoips test unit-test" command supports this format:
#             - geoips test unit-test dir_name <-p> <package_name> <-n> <test_name>
#         Where:
#             - dir_name is the name of the folder containing the unit-test[s] you want to # NOQA
#               run
#             - <package_name> is any GeoIPS package that is installed and recognized by
#               the GeoIPS Library
#             - <test_name> is the name of the unit test being ran
#         """
#         self.parser.add_argument(
#             "directory_name",
#             type=str,
#             help="GeoIPS Packages Unit Test Directory Name where unit tests are held.", # NOQA
#         )
#         self.parser.add_argument(
#             "--package-name",
#             "-p",
#             type=str,
#             default="geoips",
#             choices=self.plugin_package_names,
#             help="GeoIPS Package containing the unit-tests to be ran.",
#         )
#         self.parser.add_argument(
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
#             self.parser.error(err_str)

#         if dir_name not in listdir(unit_test_dir):
#             # The specified unit test directory does not exist at the specified location # NOQA
#             # raise an error specifying that
#             err_str = f"Directory '{dir_name}' not found under {package_name}'s unit "
#             err_str += f"tests directory '{unit_test_dir}'. Please select one of the "
#             err_str += f"following unit test directories:\n {listdir(unit_test_dir)}"
#             self.parser.error(err_str)
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
#                 err_str += f"'{unit_test_dir}', please select one of the options shown " # NOQA
#                 err_str += f"below.\ns {fnames}"
#                 self.parser.error(err_str)
#         else:
#             # script name wasn't specified, run all unit tests found under
#             # <package_name>/tests/unit_tests/<dir_name>
#             test_name = "."

#         test_path = str(f"{unit_test_dir}/{dir_name}/{test_name}")
#         invoke_pytest(["-v", test_path])


class GeoipsTestSector(GeoipsExecutableCommand):
    """Test Command for creating a sector image based on the provided sector name.

    This used to be ran via 'create_sector_image', however we are trying to consolidate
    all independent console scripts to be used via the CLI. When this command is called
    an image of the provided sector will be created so we can view whether or not it
    matches the region of the globe we'd like to study.
    """

    name = "sector"
    command_classes = []

    def add_arguments(self):
        """Instantiate the arguments that are supported for the test sector command.

        Currently the "geoips test sector" command supports this format:
            - geoips test sector <sector_name> --outdir <output_directory_path>
        Where:
            - <sector_name> is the name of any GeoIPS Sector Plugin that has an entry in
              any package's plugin registry.
            - --outdir is the full path to the directory in which you'd like to create
              the sector image.
        """
        self.parser.add_argument(
            "sector_name",
            type=str,
            help="Name of the sector plugin to create an image from.",
        )
        self.parser.add_argument(
            "--outdir",
            "-o",
            type=str,
            default=str(PATHS['GEOIPS_OUTDIRS']),
            help="The output directory to create your sector image in.",
        )
        self.parser.add_argument(
            "--overlay",
            default=False,
            action="store_true",
            help=(
                "Overlay this sector on the global_cylindrical grid. Useful for testing"
                "small sectors, where their domain might be difficult to interpret in "
                "a geospatial context."
            ),
        )

    def __call__(self, args):
        """Create the provided sector image based off the arguments provided.

        This will retrieve the selected sector plugin from any GeoIPS Plugin package,
        then create an image of that sector. This is a good way to quickly test whether
        or not your sector plugin covers the area you expected with the correct
        resolution.

        Parameters
        ----------
        args: Argparse Namespace()
            - The list argument namespace to parse through
        """
        sector_name = args.sector_name
        outdir = args.outdir
        overlay = args.overlay
        # If the path to outdir doesn't already exist, make that path
        if not exists(outdir):
            makedirs(outdir)
        # Create an image for the requested sector, including just the map and white
        # background.
        fname = join(outdir, f"{sector_name}.png")
        try:
            if "non_existent" in sector_name:
                # This occurs for a unit test that we are just checking the error output
                # for. No need to rebuild the plugin registry, which can be specified by
                # using rebuild_registries=False
                rebuild_registries = False
            else:
                # Otherwise, assume this is a new sector that is being developed, and
                # automate plugin registry creation if it does not already exist as an
                # entry in the registry.
                rebuild_registries = True
            sect = sectors.get_plugin(
                sector_name, rebuild_registries=rebuild_registries
            )
        except PluginError:
            raise self.parser.error(
                f"Sector '{sector_name}' is not a valid plugin.\nPlease use a plugin "
                "found under 'geoips list interface sectors' or create a new plugin "
                f"named '{sector_name}' and run 'create_plugin_registries'."
            )
        print(f"Creating {fname}.")
        sect.create_test_plot(fname, overlay=overlay)


class GeoipsTestScript(GeoipsExecutableCommand):
    """Test Command for running GeoIPS Test Scripts."""

    name = "script"
    command_classes = []

    def add_arguments(self):
        """Instantiate the arguments that are supported for the test script command.

        Currently the "geoips test script" command supports this format:
            - geoips test script <-p> <package_name> <script_name> <--integration>
        Where:
            - <package-name> is any GeoIPS package that is installed and recognized by
              the GeoIPS Library
            - <script_name> is the name of the bash script being tested
            - '--integration' represents whether or not this is an 'integration' test
        """
        self.parser.add_argument(
            "script_name",
            type=str,
            help="GeoIPS Script to be tested",
        )
        self.parser.add_argument(
            "--package-name",
            "-p",
            type=str,
            default="geoips",
            choices=self.plugin_package_names,
            help="GeoIPS Package containing the script to be tested",
        )
        self.parser.add_argument(
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
        if args.warnings != "print":
            warnings.warn(
                "The 'warnings' argument is not yet supported for this command.",
                UserWarning,
            )
        package_name = args.package_name
        script_name = args.script_name
        is_integration_test = args.integration

        if is_integration_test:
            if package_name != "geoips":
                # Raise an argparse error which states only geoips supports integration
                # testing
                err_str = "Only package 'geoips' has integration tests. Package "
                err_str += f"'{package_name}' doesn't have those tests. Try again."
                self.parser.error(err_str)
            dir_name = "integration_tests"
        else:
            dir_name = "scripts"
        if not is_editable(package_name):
            # Package is installed in non-editable mode and we will not be able to
            # access unit tests. Raise a runtime error reporting this.
            print(
                f"Error: Package '{package_name}' is installed in non-editable mode and"
                " we are not able to access it's unit tests. For this command to "
                f"work, please install '{package_name}' in editable mode via: "
                f"'pip install -e <path_to_{package_name}>'",
                file=sys.stderr,
            )
            # We use a print to sys.stderr so monkeypatch unit tests can catch this
            # output
            raise RuntimeError(
                f"Package '{package_name}' isn't installed in editable mode."
            )
        test_dir = str(resources.files(package_name) / f"../tests/{dir_name}")
        fnames = [basename(fpath) for fpath in glob(f"{test_dir}/*.sh")]

        if script_name not in fnames:
            # Raise an argparse error which states that file doesn't exist within the
            # specified directory
            str_fnames = ",\n".join(fnames)
            err_str = f"Script '{script_name}' doesn't exist within '{test_dir}/'. "
            err_str += "Please select a valid script from this directory listing:\n"
            err_str += str_fnames
            self.parser.error(err_str)

        script_path = f"{test_dir}/{script_name}"
        # Run the corresponding test
        call(["bash", script_path], shell=False)


class GeoipsTestLinting(GeoipsExecutableCommand):
    """Test Command for running GeoIPS Linting Services."""

    name = "linting"
    command_classes = []

    def add_arguments(self):
        """Add arguments to the test-subparser for the Test Linting Command."""
        self.parser.add_argument(
            "--package-name",
            "-p",
            type=str,
            default="geoips",
            choices=self.plugin_package_names,
            help="GeoIPS Package that we want to run linting tests on.",
        )

    def __call__(self, args):
        """Run all GeoIPS Linting Tests on the provided package."""
        package_name = args.package_name
        if not is_editable(package_name):
            # Package is installed in non-editable mode and we will not be able to
            # access unit tests. Raise a runtime error reporting this.
            print(
                f"Error: Package '{package_name}' is installed in non-editable mode and"
                " we are not able to access it's unit tests. For this command to "
                f"work, please install '{package_name}' in editable mode via: "
                f"'pip install -e <path_to_{package_name}>'",
                file=sys.stderr,
            )
            # We use a print to sys.stderr so monkeypatch unit tests can catch this
            # output
            raise RuntimeError(
                f"Package '{package_name}' isn't installed in editable mode."
            )
        lint_path = str(resources.files("geoips") / "../tests/utils/check_code.sh")
        package_path = str(resources.files(package_name) / "../.")
        for linter in ["bandit", "black", "flake8"]:
            call(["bash", lint_path, linter, package_path], shell=False)


class GeoipsTest(GeoipsCommand):
    """Top-Level test command for testing GeoIPS and its corresponding packages."""

    name = "test"
    command_classes = [GeoipsTestLinting, GeoipsTestScript, GeoipsTestSector]
    # command_classes = [GeoipsTestLinting, GeoipsTestScript, GeoipsTestUnitTest]
