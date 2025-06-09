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
    for step_id, step_def in wf.spec.steps.items():
        interface = step_def.kind + "s"

        if interface not in handled_interfaces:
            LOG.interactive(
                "⚠️ Skipping unhandled interface '%s'. Would have called the '%s'"
                "plugin.",
                interface,
                step_def.name,
            )
            continue
        else:
            plg = getattr(interfaces, interface, None).get_plugin(step_def.name)
            LOG.interactive(
                "Beginning Step: '%s', plugin_kind: '%s', plugin_name:'%s'.",
                step_id,
                step_def.kind,
                step_def.name,
            )
            LOG.info("Arguments: '%s'", step_def.arguments)

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
                "Completed Step: step_id: '%s', plugin_kind: '%s', plugin_name: '%s'.",
                step_id,
                step_def.name,
                step_def.kind,
            )

    LOG.interactive(f"\nThe workflow '{workflow}' has finished processing.\n")


if __name__ == "__main__":

    parser = ArgumentParser(description="order-based procflow processing")
    parser.add_argument("workflow", help="The workflow name to process.")
    parser.add_argument("fnames", nargs="+", help="The filenames to process.")
    args = parser.parse_args()
    call(args.workflow, args.fnames)
