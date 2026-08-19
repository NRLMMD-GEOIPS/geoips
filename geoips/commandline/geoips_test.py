# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""GeoIPS CLI "test" command.

Runs the appropriate tests based on the arguments provided.
"""

from glob import glob
from importlib import resources
import logging
from os import makedirs
from os.path import basename, exists, join
import sys
import warnings

# from pytest import main as invoke_pytest
from subprocess import call

from geoips.commandline.geoips_command import (
    GeoipsCommand,
    GeoipsExecutableCommand,
    GeoipsWorkflowCommand,
)
from geoips.errors import PluginError
from geoips.filenames.base_paths import PATHS
from geoips.geoips_utils import is_editable
from geoips.interfaces import procflows, sectors, workflows

LOG = logging.getLogger(__name__)

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
            default=PATHS["GEOIPS_OUTDIRS"],
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
        self.parser.add_argument(
            "--gridlines",
            "-g",
            default=False,
            action="store_true",
            help="Add a latitude / longitude gridline overlay to your sector.",
        )
        self.parser.add_argument(
            "--labels",
            "-l",
            default=["left", "bottom"],
            choices=["left", "right", "top", "bottom"],
            nargs="*",
            help=(
                "A list of strings which set where gridline labels will be set on the "
                "sector. Specify no values to disable labels."
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
        gridlines = args.gridlines
        labels = args.labels
        noborder = False if len(labels) else True

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
                f"named '{sector_name}' and run 'pluginify create'."
            )
        print(f"Creating {fname}.")
        sect.create_test_plot(
            fname,
            overlay=overlay,
            gridlines=gridlines,
            gridline_labels=labels,
            noborder=noborder,
        )


class GeoipsTestWorkflow(GeoipsWorkflowCommand):
    """Command class for testing a workflow plugin.

    If a workflow plugin has a ``test`` section at the same level as ``spec``, then this
    command can be ran to test the output of a workflow plugin. The ``test`` section
    should include all parameters needed to produce a replicable output which can be
    created by executing all the steps listed in the given workflow.
    """

    name = "workflow"
    command_classes = []

    def add_arguments(self):
        """Add arguments to the describe-subparser for the describe Interface cmd."""
        self.parser.add_argument(
            "workflow",
            type=self.workflow_type,
            help=(
                "Workflow instance. Can be the name of a registered workflow plugin, "
                "a .json or .yaml path to an unregistered workflow plugin, or a "
                "dictionary that will be literally evaluated as a workflow."
            ),
        )

    def __call__(self, args):
        """CLI 'geoips test workflow <workflow_type>' command.

        This occurs when a user attempts to test the output of a select workflow plugin.

        This command will not proceed if the workflow plugin is missing a ``test``
        section specifying the parameters needed to properly test the given workflow.

        Printed to Terminal
        -------------------
        test output: str
            - The captured print and log statements from executing a given workflow.

        Parameters
        ----------
        args: Argparse Namespace()
            - The list argument namespace to parse through
        """
        workflow = args.workflow

        try:
            test_section = workflow["test"]
        except KeyError:
            test_section = None

        if test_section is None:
            self.parser.error(
                f"Error: cannot test '{workflow['name']}' workflow plugin as it is "
                "missing a ``test`` section. Please create this content before "
                "attempting to test this plugin again."
            )

        fnames = test_section.get("filenames", test_section.get("fnames", []))
        LOG.info(
            "Testing workflow %r with %d input file(s).",
            workflow["name"],
            len(fnames),
        )
        LOG.debug("Workflow test input files: %s", fnames)
        workflow = workflows._override_expanded_workflow(workflow)

        obp = procflows.get_plugin("order_based")

        # TODO: Add additional logic here for other parameters included in a workflow
        # test section, such as 'compare_path'. 'overrides' section not passed to obp
        # as the override has already been applied to the workflow plugin.
        obp(workflow_spec=workflow, filenames=fnames)


class GeoipsTest(GeoipsCommand):
    """Top-Level test command for testing GeoIPS and its corresponding packages."""

    name = "test"

    command_classes = [
        GeoipsTestLinting,
        GeoipsTestScript,
        GeoipsTestSector,
        GeoipsTestWorkflow,
    ]
