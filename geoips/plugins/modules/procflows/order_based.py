"""Processing workflow for order based data source processing."""

# Python Standard Libraries
from argparse import ArgumentParser

# Third-Party Libraries
import yaml

# GeoIPS imports
from geoips import interfaces
from geoips.pydantic.products import ProductPluginModel

interface = "procflows"
family = "standard"
name = "order_based"


def call(
    fnames: list[str], product_name: str, command_line_args: list[str] | None = None
) -> None:
    """Run the order based procflow (OBP).

    Process the specified input data files using the OBP in the order of steps
    listed in the product definition file.

    Parameters
    ----------
    fnames : list of str
        list of filenames to process
    product_name : str
        path to the product definition file
    command_line_args : list of str, None
        fnames & product-path
    """
    with open(product_name) as product_definition_file:
        prod_dict = yaml.safe_load(product_definition_file)
        prod = ProductPluginModel(**prod_dict)

    for step in prod.spec.steps:
        step_def = step.definition
        print(
            # f"\n\nstep\t {step} \n\nplugin \n\t"
            # f"\n\t step_name : {step_def.step_name}"
            f"\n\t type : {step_def.type}"
            f"\n\t name : {step_def.name} \n\t arguments : {step_def.arguments}"
        )

        interface = step_def.type + "s"

        # the if-else ladder will go away after all steps are implemented
        plugin_instance = getattr(interfaces, interface, None).get_plugin(step_def.name)
        if interface == "readers":
            print(
                f"\n\n{step_def.type} processing details:\n\n\t"
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


if __name__ == "__main__":

    parser = ArgumentParser(description="order-based procflow processing")
    parser.add_argument("fnames", nargs="+", help="The filenames to process.")
    parser.add_argument(
        "-p", "--product_name", help="The path to the product definition file."
    )
    args = parser.parse_args()
    call(args.fnames, args.product_name)
