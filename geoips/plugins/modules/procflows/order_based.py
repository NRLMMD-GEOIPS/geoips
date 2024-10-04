from argparse import ArgumentParser
import yaml

from IPython import embed as shell

from geoips.pydantic.products import ProductPlugin
from geoips import interfaces
# from geoips.interfaces import products


# from geoips.interfaces import products
# products.get_plugin(product_name)
interface = "procflows"
family = "standard"
name = "order_based"

def call(fnames: list[str], product_path: str, command_line_args: list[str] | None = None) -> None:
    """
    runs an order-based procflow processing with the specified input data files & product definition file
    
        Parameters:
            fnames (list[str]): list of filenames to process
            product-path (str): path to the product definition file
            command_line_args (list[str] | None, optional): fnames & product-path via CLI

        Returns:
            None
    """
    with open(product_path) as product_definition_file:
        prod_dict = yaml.safe_load(product_definition_file)
        prod = ProductPlugin(**prod_dict)
        print(prod)
    
    print(f"interface: {prod.get_interface()}")
    print(f"reader: {prod.get_reader()}")
    print(f"variables: {prod.get_reader_variables()}")
    
    interface = prod.get_interface()
    # reader = interfaces.products.get_plugin(prod.get_interface())
    # reader = interface.get_plugin(step.reader)

    

if __name__ == "__main__":
    parser = ArgumentParser(description="order-based procflow processing")
    parser.add_argument("fnames", nargs="+", help="The filenames to process.")
    parser.add_argument(
        "-p", "--product_path", help="The path to the product definition file."
    )

    args = parser.parse_args()

    call(args.fnames, args.product_path)

