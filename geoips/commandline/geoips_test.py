# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""GeoIPS CLI "test" command.

Runs the appropriate tests based on the arguments provided.
"""

import logging

from geoips.commandline.geoips_command import (
    GeoipsCommand,
    GeoipsWorkflowCommand,
)
from geoips.interfaces import procflows, workflows

LOG = logging.getLogger(__name__)


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

    command_classes = [GeoipsTestWorkflow]
