# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Simple script to list available plugins for each interface."""

import warnings
from geoips.interfaces.base import BaseInterface
from geoips import interfaces
from geoips.commandline.log_setup import setup_logging
from geoips.commandline.args import get_argparser, check_command_line_args

# Always actually raise DeprecationWarnings
# Note this SO answer https://stackoverflow.com/a/20960427
warnings.simplefilter("always", DeprecationWarning)


def main():
    """Script to list all modules available in the current geoips instantiation."""
    supported_args = ["logging_level"]

    # Use standard GeoIPS argparser - use standard formatting for standard args.
    parser = get_argparser(
        arglist=supported_args,
        description="List available plugins within the current geoips instantiation.",
    )
    # Add our specific "interfaces" argument.
    parser.add_argument(
        "interfaces",
        nargs="*",
        default=None,
        help="""List of interfaces to include.  If None, include all interfaces.""",
    )

    # Get the dictionary of command line args.
    COMMAND_LINE_ARGS = parser.parse_args().__dict__
    # Check included arguments for appropriate formatting / type.
    check_command_line_args(supported_args, COMMAND_LINE_ARGS)

    # Setup logging at the requested logging level.
    LOG = setup_logging(logging_level=COMMAND_LINE_ARGS["logging_level"])

    # If "interfaces" is not specified command line, then include plugins for
    # all interfaces.
    if not COMMAND_LINE_ARGS["interfaces"]:
        curr_interfaces = interfaces.__dict__.values()
    else:
        curr_interfaces = [
            interfaces.__dict__[curr_interface]
            for curr_interface in COMMAND_LINE_ARGS["interfaces"]
        ]

    # Print just the interface name and plugin name for each plugin in each
    # requested interface.
    for curr_interface in curr_interfaces:
        if (type(curr_interface) is BaseInterface) or not isinstance(
            curr_interface, BaseInterface
        ):
            continue

        # This prints a "horizontal line" character U+2015, not a dash
        LOG.interactive("―" * len(curr_interface.name))
        LOG.interactive(f"{curr_interface.name}")
        LOG.interactive("―" * len(curr_interface.name))
        plugin_names = sorted([plg.name for plg in curr_interface.get_plugins()])
        LOG.interactive(", ".join(plugin_names))


if __name__ == "__main__":
    main()
