#!/usr/bin/env python

# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""GeoIPS command line interface."""

import pkgutil
from argparse import (
    ArgumentParser,
    ArgumentDefaultsHelpFormatter,
    RawDescriptionHelpFormatter,
)
from geoips import dev, interfaces
from geoips.interfaces.base import BaseInterface
import warnings
import logging

# Always actually raise DeprecationWarnings
# Note this SO answer https://stackoverflow.com/a/20960427
warnings.simplefilter("always", DeprecationWarning)
LOG = logging.getLogger(__name__)

__doc__ = """
GeoIPS

The Geolocated Information Processing System (GeoIPS) is a generalized
processing system, providing a collection of algorithm and product
implementations facilitating consistent and reliable application of specific
products across a variety of sensors and data types.

GeoIPS acts as a toolbox for internal GeoIPS-based product development - all
modules are expected to have simple inputs and outputs (Python numpy or dask
arrays or xarrays, dictionaries, strings, lists), to enable portability and
simplified interfacing between modules.
"""


class RawDescriptionArgumentDefaultsHelpFormatter(
    ArgumentDefaultsHelpFormatter, RawDescriptionHelpFormatter
):
    """Compound formatter class for user-readable help.

    * preserves the raw description formatting
    * adds defaults to helps.
    """

    pass


formclass = RawDescriptionArgumentDefaultsHelpFormatter


def print_table(title, headings, rows):
    """Print a column formatted table.

    Parameters
    ----------
    title : str
        A title for the table
    headings : list of str
        A list of strings to use as column headings
    rows : list of tupl of str
        A list of equal-length tuples
    """
    ncol = len(headings)
    rows = list(rows)
    for row_ind, row in enumerate(rows):
        if len(row) != ncol:
            raise ValueError("Number of elements per row must be equal for all rows")
        rows[row_ind] = [str(val) if val is not None else "" for val in row]

    col_widths = []
    for col_ind, heading in enumerate(headings):
        col_width = len(heading)
        for row in rows:
            col_width = max(col_width, len(row[col_ind]))
        col_widths.append(col_width)

    title_case_title = title.replace("_", " ").title()
    title_width = sum(col_widths) + 3 * (len(col_widths) - 1)
    LOG.info("\n" + title_width * "=")
    LOG.info(f"{title_case_title:^{title_width}}")
    LOG.info(title_width * "=")

    # Create and print the header
    head_str = " | ".join(
        [f"{head:{width}}" for head, width in zip(headings, col_widths)]
    )
    LOG.info(head_str)
    LOG.info(len(head_str) * "-")

    # Create and print the rows
    for row in rows:
        # print(list(zip(row, col_widths)))
        row_str = " | ".join([f"{val:{width}}" for val, width in zip(row, col_widths)])
        LOG.info(row_str)


def get_interface(name):
    """Get interface."""
    try:
        return getattr(interfaces, name)
    except AttributeError:
        try:
            return getattr(dev, name)
        except AttributeError:
            raise AttributeError(f'Interface "{name}" not found')


def add_list_interface_parser(subparsers, name, aliases=None):
    """Add list interface parser."""
    # list interpolators
    interface_parser = subparsers.add_parser(
        name,
        aliases=aliases,
        description=f"List available {name}",
        help=f"List available {name}",
        formatter_class=formclass,
    )
    interface_parser.set_defaults(interface=name)
    return interface_parser


def list_dev_interfaces():
    """Return a list of all developmental interfaces."""
    return [name for _, name, _ in pkgutil.iter_modules(dev.__path__)]


def list_interfaces(dev=False):
    """List interfaces."""
    inter_names = []
    inter_descs = []
    for attr in dir(interfaces):
        attr_val = getattr(interfaces, attr)
        if issubclass(attr_val.__class__, BaseInterface):
            inter_names.append(attr_val.name)
            try:
                inter_descs.append(getattr(attr_val, "__doc__").splitlines()[0])
            except AttributeError:
                inter_descs.append("")

    headers = ["name", "description"]
    inter_rows = zip(inter_names, inter_descs)

    print_table("New-Style Interfaces", headers, inter_rows)

    print_table("Old-Style Interfaces", ["Name"], zip(list_dev_interfaces()))


def list_interface_plugins(interface_name):
    """List interface plugins."""
    inter = get_interface(interface_name)
    plugins = inter.get_plugins()
    rows = [(pl.name, pl.family, pl.description) for pl in plugins]
    print_table(interface_name, ["Name", "Family", "Description"], rows)


# def print_interface_list(inter):
#     mod_list = inter.get_plugins()
#
#     # Determine column widths for output
#     ncol = len(mod_list[0])
#     headings = ['name', 'type', 'description']
#     if ncol != len(headings):
#         raise ValueError('Number of columns does not match the number of headings')
#     col_widths = [len(head) for head in headings]
#     for mod in mod_list:
#         for col in range(len(mod)):
#             col_widths[col] = max(col_widths[col], len(mod[col]))
#     # col_widths = [wid + 1 for wid in col_widths]
#     print(col_widths)
#
#     # Create and print the header
#     head_vals = []
#     for head_val, width in zip(headings, col_widths):
#         head_vals.append(f'{head_val:{width}}')
#     head_str = ' | '.join(head_vals)
#     print(head_str)
#     print(len(head_str) * '-')
#
#     # Create and print the rows
#     for mod in mod_list:
#         mod_vals = []
#         for mod_val, width in zip(mod, col_widths):
#             mod_vals.append(f'{mod_val:{width}}')
#         mod_str = ' | '.join(mod_vals)
#         print(mod_str)


def main():
    """Command line interface main function."""
    parser = ArgumentParser(description=__doc__, formatter_class=formclass)
    subparsers = parser.add_subparsers(
        title="Commands", description="GeoIPS commands", dest="cmd"
    )

    # run command
    run_parser = subparsers.add_parser(
        "run",
        description="Run a GeoIPS procflow",
        help="Run a GeoIPS procflow",
        formatter_class=formclass,
    )
    run_parser.add_argument("test")

    # list command
    list_parser = subparsers.add_parser(
        "list",
        description="List available interfaces",
        help="List available interfaces",
        formatter_class=formclass,
    )

    # Don't use `dest` here. It doesn't work well with aliases
    # Instead use `set_defaults` on each parser like below
    # See here for more info:
    #    https://bugs.python.org/issue36664
    list_subparsers = list_parser.add_subparsers()

    # list interfaces
    add_list_interface_parser(list_subparsers, "interfaces", aliases=["int", "ints"])

    # list plugins for each interface
    add_list_interface_parser(list_subparsers, "algorithms", aliases=["alg", "algs"])
    # add_list_interface_parser(
    #     list_subparsers, "feature_annotators", aliases=["bound", "bounds"]
    # )
    add_list_interface_parser(
        list_subparsers, "colormappers", aliases=["cmap", "cmaps"]
    )
    add_list_interface_parser(
        list_subparsers, "filename_formatters", aliases=["ff", "ffs"]
    )
    # add_list_interface_parser(
    #     list_subparsers, "gridline_annotators", aliases=["gf", "gfs"]
    # )
    add_list_interface_parser(
        list_subparsers, "interpolators", aliases=["interp", "interps"]
    )
    # add_list_interface_parser(
    #     list_subparsers, "outputter_configs", aliases=["oc", "ocs"]
    # )
    add_list_interface_parser(
        list_subparsers, "output_formatters", aliases=["out", "outs"]
    )
    add_list_interface_parser(list_subparsers, "procflows", aliases=["pf", "pfs"])
    # add_list_interface_parser(list_subparsers, 'products', aliases=['prod', 'prods'])
    add_list_interface_parser(list_subparsers, "readers", aliases=["reader"])
    add_list_interface_parser(
        list_subparsers, "title_formatters", aliases=["tf", "tfs"]
    )

    args = parser.parse_args()

    if args.cmd == "list":
        if args.interface == "interfaces":
            list_interfaces()
        else:
            list_interface_plugins(args.interface)
            # print(get_interface(args.interface))
            # print(get_interface(args.interface).get_plugins())
            # getattr(interfaces, args.interface).get_plugins(
            #     pretty=True, with_family=True, with_description=True
            # )


if __name__ == "__main__":
    main()
