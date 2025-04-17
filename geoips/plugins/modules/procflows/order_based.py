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


def call(workflow, fnames, command_line_args=None):
    """Run the order based procflow (OBP).

    Process the specified input data files using the OBP in the order of steps
    listed in the workflow definition file.

    Parameters
    ----------
    workflow: str
        The name of the workflow to process.
    fnames : list of str
        List of filenames from which to read data.
    command_line_args : list of str, None
        Command line arguments to pass to the workflow.
    """
    LOG.interactive(f"Begin processing '{workflow}' workflow.")
    wf_plugin = interfaces.workflows.get_plugin(workflow)
    wf = WorkflowPluginModel(**wf_plugin)

    handled_interfaces = ["readers"]
    for step in wf.spec.steps:
        step_def = step.definition
        #  Tab spaces and newline escape sequences will be removed later.
        #  I added them for formatting purposes and the reviewer's convenience.
        #  The severity level will eventually be moved to info.
        interface = step_def.type + "s"

        if interface not in handled_interfaces:
            LOG.interactive(
                "Skipping unhandled interface '%s'. Would have called the '%s' plugin.",
                interface,
                step_def.name,
            )
            continue
        else:
            plg = getattr(interfaces, interface, None).get_plugin(step_def.name)
            LOG.interactive(
                "Calling %s %s plugin with the following arguments: \n\t%s",
                step_def.name,
                step_def.type,
                step_def.arguments,
            )
            if interface == "readers":
                # TEMPORARY FIX: Remove when all readers are updated to accept
                # "variables"
                if "variables" in step_def.arguments:
                    step_def.arguments["chans"] = step_def.arguments.pop("variables")
                data = plg(fnames, **step_def.arguments)
                print(data)
            else:
                data = plg(data, **step_def.arguments)
            LOG.interactive(
                "Finished %s %s plugin.",
                step_def.name,
                step_def.type,
            )

    LOG.interactive(f"The workflow '{workflow}' has finished processing.")


if __name__ == "__main__":

    parser = ArgumentParser(description="order-based procflow processing")
    parser.add_argument("workflow", help="The workflow name to process.")
    parser.add_argument("fnames", nargs="+", help="The filenames to process.")
    args = parser.parse_args()
    call(args.workflow, args.fnames)
