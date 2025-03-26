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


# def call(fnames, product_name, command_line_args=None):


def call(
    fnames: list[str], product_name: str, command_line_args: list[str] | None = None
) -> None:
    """Run the order based procflow (OBP).

    Process the specified input data files using the OBP in the order of steps
    listed in the workflow definition file.

    Parameters
    ----------
    fnames : list of str
        list of filenames to process
    product_name : str
        product name to process
    command_line_args : list of str, None
        fnames and product-name
    """
    LOG.interactive(f"The product : '{product_name}' has begun processing.")
    prod_plugin = interfaces.workflows.get_plugin(product_name)
    prod = WorkflowPluginModel(**prod_plugin)

    for step in prod.spec.steps:
        step_def = step.definition
        #  Tab spaces and newline escape sequences will be removed later.
        #  I added them for formatting purposes and the reviewer's convenience.
        #  The severity level will eventually be moved to info.
        LOG.interactive(
            f"\n\t type : {step_def.type} \n\t name : {step_def.name}"
            f"\n\t arguments : {step_def.arguments}"
        )

        interface = step_def.type + "s"

        # the if-else ladder will go away after all steps are implemented
        if interface == "readers":
            plugin_instance = getattr(interfaces, interface, None).get_plugin(
                step_def.name
            )
            #  Tab spaces and newline escape sequences will be removed later.
            #  I added them for formatting purposes and the reviewer's convenience.
            #  The severity level will eventually be moved to info.
            LOG.interactive(
                f"\t {step_def.type} processing details:\n\n\t"
                f"{plugin_instance(fnames, step_def.arguments)}\n\n"
            )
        elif interface == "algorithms":
            pass
        elif interface == "interpolators":
            pass
        elif interface == "output_formatter":
            pass
        else:
            pass
    LOG.interactive(f"The product : '{product_name}' has finished processing.")


if __name__ == "__main__":

    parser = ArgumentParser(description="order-based procflow processing")
    parser.add_argument("fnames", nargs="+", help="The filenames to process.")
    parser.add_argument("-p", "--product_name", help="The product name to process.")
    args = parser.parse_args()
    call(args.fnames, args.product_name)
