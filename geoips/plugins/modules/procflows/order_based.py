"""Processing workflow for order based data source processing."""

from argparse import ArgumentParser
import yaml

from geoips import interfaces
from geoips.pydantic.products import ProductPlugin


interface = "procflows"
family = "standard"
name = "order_based"


def call(
    fnames: list[str], product_path: str, command_line_args: list[str] | None = None
) -> None:
    """Runs an OBP processing with the specified input data files &
    steps listed in product definition file (PDF).

    Parameters
    ----------
        * fnames (list[str]): list of filenames to process
        * product-path (str): path to the product definition file
        * command_line_args (list[str] | None, optional): fnames & product-path

    Returns
    -------
        * None
    """
    with open(product_path) as product_definition_file:
        prod_dict = yaml.safe_load(product_definition_file)
        prod = ProductPlugin(**prod_dict)
        print("prod is \t", prod)

    for step in prod.spec.steps:
        print(
            f"\n\nstep\t {step} \nplugin in OBP\n\t type : {step.type} \n\t name: {step.name} \n\t arguments: step.arguments"
        )

        interface = step.type + "s"

        if interface == "readers":
            reader = getattr(interfaces, interface, None).get_plugin(step.name)
            data = reader(fnames)
            print(f"reader data is \n\t, {data}")
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
    parser.add_argument("-p", "--product_path", help="The path to the PDF.")

    args = parser.parse_args()
    call(args.fnames, args.product_path)
