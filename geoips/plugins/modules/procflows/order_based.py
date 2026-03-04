# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Processing workflow for order based data source processing."""

# Python Standard Libraries
from argparse import ArgumentParser
import logging

# Third-Party Libraries
import xarray as xr
from xarray import DataTree

# GeoIPS imports
from geoips import interfaces
from geoips.commandline.log_setup import setup_logging
from geoips.utils.types.partial_lexeme import Lexeme

LOG = logging.getLogger(__name__)

interface = "procflows"
family = "standard"
name = "order_based"


def xarray_datatree_to_dataset(data, node="MED"):
    if (
        hasattr(data, "__class__")
        and data.__class__.__name__ == "DataTree"
    ):
        return data[node].ds
    return data


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
    LOG.interactive(f"Begin processing '{workflow['name']}' workflow.")
    wf_plugin = workflow

    handled_interfaces = ["readers", "coverage_checkers", "interpolators"]
    for step_id, step_def in wf_plugin["spec"]["steps"].items():
        interface = str(Lexeme(step_def["kind"]).plural)

        if interface not in handled_interfaces:
            LOG.interactive(
                "⚠️ Skipping unhandled interface '%s'. Would have called the '%s'"
                "plugin.",
                interface,
                step_def["name"],
            )
            continue
        else:
            plg = getattr(interfaces, interface, None).get_plugin(step_def["name"])

            LOG.interactive(
                "Beginning Step: '%s', plugin_kind: '%s', plugin_name:'%s'.",
                step_id,
                step_def["kind"],
                step_def["name"],
            )
            LOG.info("Arguments: '%s'", step_def["arguments"])

            if interface == "readers":
                # TEMPORARY FIX: Remove when all readers are updated to accept
                # "variables"
                if "variables" in step_def["arguments"]:
                    step_def["arguments"]["chans"] = step_def["arguments"].pop(
                        "variables"
                    )
                data = plg(fnames, **step_def["arguments"])
                data_xr_dt = DataTree.from_dict(data)

                if step_id not in data_xr_dt:
                    data_xr_dt[step_id] = DataTree()

                for name in list(data_xr_dt.children.keys()):
                    if name == "METADATA" or name == step_id:
                        continue

                    data_xr_dt[f"{step_id}/{name}"] = data_xr_dt[name].ds
                    del data_xr_dt[name]


                input_xarray = xarray_datatree_to_dataset(
                    data_xr_dt, node=f"{step_id}/MED"
                )
            elif interface == "interpolators":

                if step_id not in data_xr_dt:
                    data_xr_dt[step_id] = DataTree()

                data_xr_dt[f"{step_id}/output_interpolated_xr_ds"] = xr.Dataset()

                # area_def = "goes_east_subsector"
                area_def = input_xarray["B01Rad"]
                varlist = input_xarray["B01Rad"]

                data = plg(
                    area_def=area_def,
                    input_xarray=input_xarray,
                    output_xarray=data_xr_dt[f"{step_id}/output_interpolated_xr_ds"].ds,
                    varlist=varlist,
                    **step_def["arguments"],
                )
                # ['LOW', 'METADATA', 'output_xarray']
            LOG.interactive(
                "Completed Step: step_id: '%s', plugin_kind: '%s', plugin_name: '%s'.",
                step_id,
                step_def["name"],
                step_def["kind"],
            )

    LOG.interactive(f"\nThe workflow '{workflow}' has finished processing.\n")


if __name__ == "__main__":

    parser = ArgumentParser(description="order-based procflow processing")
    parser.add_argument("workflow", help="The workflow name to process.")
    parser.add_argument("fnames", nargs="+", help="The filenames to process.")
    parser.add_argument(
        "-l",
        "--loglevel",
        choices=["debug", "info", "interactive", "warning", "error"],
        default="interactive",
    )
    args = parser.parse_args()
    LOG = setup_logging(logging_level=args.loglevel)
    call(interface.workflows.get_plugin(args.workflow), args.fnames)
