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
