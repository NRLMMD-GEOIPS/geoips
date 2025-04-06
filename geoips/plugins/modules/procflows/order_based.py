"""Processing workflow for order based data source processing."""

# Python Standard Libraries
from argparse import ArgumentParser
import logging

# GeoIPS imports
from geoips import interfaces
from geoips.pydantic.workflows import WorkflowPluginModel

LOG = logging.getLogger(__name__)

interface = "procflows"
family = "standard"
name = "order_based"


def call(fnames, workflow_name, command_line_args=None):
    """Run the order based procflow (OBP).

    Process the specified input data files using the OBP in the order of steps
    listed in the workflow definition file.

    Parameters
    ----------
    fnames : list of str
        list of filenames to process
    workflow_name : str
        workflow name to process
    command_line_args : list of str, None
        fnames and workflow-name
    """
    LOG.interactive(f"The workflow : '{workflow_name}' has begun processing.")
    workflow_plugin = interfaces.workflows.get_plugin(workflow_name)
    workflow = WorkflowPluginModel(**workflow_plugin)

    for step in workflow.spec.steps:
        step_def = step.definition
        #  Tab spaces and newline escape sequences will be removed later.
        #  I added them for formatting purposes and the reviewer's convenience.
        #  The severity level will eventually be moved to info.
        LOG.interactive(
            f"\n\t type : {step_def.type} \n\t name : {step_def.name}"
            f"\n\t arguments : {step_def.arguments}"
        )

        interface = step_def.type + "s"

        handled_types = ["readers", "workflows"]

        if interface in handled_types:
            plugin_instance = getattr(interfaces, interface, None).get_plugin(
                step_def.name
            )
            LOG.interactive(
                f"\t {step_def.type} processing details:\n\n\t"
                f"{plugin_instance(fnames, step_def.arguments)}\n\n"
            )
        else:
            LOG.interactive(f"[!] Unhandled plugin type '{interface}' encountered")

    LOG.interactive(f"The workflow : '{workflow_name}' has finished processing.")


if __name__ == "__main__":

    parser = ArgumentParser(description="order-based procflow processing")
    parser.add_argument("fnames", nargs="+", help="The filenames to process.")
    parser.add_argument("-w", "--workflow_name", help="The workflow name to process.")
    args = parser.parse_args()
    call(args.fnames, args.workflow_name)
