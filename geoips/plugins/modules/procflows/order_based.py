from argparse import ArgumentParser
import yaml
from geoips.pydantic.products import ProductPlugin
from geoips import interfaces
from IPython import embed as shell

# from geoips.interfaces import products
#
# products.get_plugin(product_name)


interface = "procflows"
family = "standard"
name = "order_based"


def call(fnames: list[str], product_path: str, command_line_args: list[str] | None = None) -> None:
    """
    runs an order-based procflow processing with the specified input data files & product definition file
    
        Parameters:
            fnames (List[str]): list of filenames to process
            product-path (str): path to the product definition file

        Returns:
            None
    """
    with open(product_path) as f:
        prod_dict = yaml.safe_load(f)
        prod = ProductPlugin(**prod_dict)

    for step in prod.spec.steps:
        print(step.interface)
        print(step.reader)
        print(step.arguments)

        # Maybe we should add a "get_interface" function rather than requiring
        # `getattr`?
        interface = getattr(interfaces, step.interface)

        reader = interface.get_plugin(step.reader)
        shell()


if __name__ == "__main__":
    parser = ArgumentParser(description="order-based procflow processing")
    parser.add_argument("fnames", nargs="+", help="The filenames to process.")
    parser.add_argument(
        "-p", "--product_path", help="The path to the product definition file."
    )

    args = parser.parse_args()

    call(args.fnames, args.product_path)

