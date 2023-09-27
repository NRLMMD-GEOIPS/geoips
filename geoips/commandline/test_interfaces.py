# # # Distribution Statement A. Approved for public release. Distribution unlimited.
# # #
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # #
# # # This program is free software: you can redistribute it and/or modify it under
# # # the terms of the NRLMMD License included with this program. This program is
# # # distributed WITHOUT ANY WARRANTY; without even the implied warranty of
# # # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the included license
# # # for more details. If you did not receive the license, for more information see:
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/

"""Simple test script to run "test_interface" for each interface."""
import pprint
import traceback
from geoips import interfaces
from geoips.interfaces.base import BaseInterface
from geoips.commandline.log_setup import setup_logging
from geoips.commandline.args import get_argparser, check_command_line_args

FAILED_INTERFACE_HEADER_PRE = "FAILED: issues found within "
FAILED_INTERFACE_HEADER_POST = "interface:"


def main():
    """Script to test all plugins in all interfaces."""
    supported_args = ["logging_level"]

    # Use standard GeoIPS argparser - use standard formatting for standard args.
    parser = get_argparser(
        arglist=supported_args,
        description="Test all interfaces within the current geoips instantiation.",
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

    failed_interfaces = []
    failed_plugins = []
    successful_interfaces = []
    successful_plugins = []
    failed_plugins_errors = []
    failed_plugins_tracebacks = []

    # If "interfaces" is not specified command line, then include plugins for
    # all interfaces.
    if not COMMAND_LINE_ARGS["interfaces"]:
        curr_interfaces = interfaces.__dict__.values()
    else:
        curr_interfaces = [
            interfaces.__dict__[curr_interface]
            for curr_interface in COMMAND_LINE_ARGS["interfaces"]
        ]

    out_dicts = {}

    # Loop through all requested interfaces, fully testing all plugins in each.
    # Collect output in lists, so we can fully print everything at the end before
    # raising an exception on error.
    for curr_interface in curr_interfaces:
        # Do not test "BaseInterface"
        if (type(curr_interface) is BaseInterface) or not isinstance(
            curr_interface, BaseInterface
        ):
            continue

        LOG.info("")
        LOG.interactive(f"Testing {curr_interface.name}...")

        # Open all the interfaces (not just checking call signatures)
        # This returns a dictionary of all sorts of stuff.
        try:
            out_dict = curr_interface.test_interface()
            out_dicts[curr_interface.name] = out_dict
        except Exception as resp:
            LOG.info(traceback.format_exc())
            failed_plugins += [curr_interface.name]
            # Collect tracebacks and errors in lists, will print everything at the end
            # prior to raising the exception.
            failed_plugins_tracebacks += [
                f"\n\n\n{FAILED_INTERFACE_HEADER_PRE} '{curr_interface.name}' "
                f"{FAILED_INTERFACE_HEADER_POST}\n\n"
                f"{traceback.format_exc()}"
            ]
            failed_plugins_errors += [
                f"\n\n\n{FAILED_INTERFACE_HEADER_PRE} '{curr_interface.name}' "
                f"{FAILED_INTERFACE_HEADER_POST}\n\n"
                f"{str(resp)}"
            ]

    # Collect lists of the successful and failed plugins (without actual errors)
    for intname in out_dicts:
        LOG.info("%s", pprint.pformat(out_dict))
        out_dict = out_dicts[intname]
        if out_dict["all_valid"] is True:
            successful_interfaces += [intname]
        else:
            failed_interfaces += [intname]
        for modname in out_dict["validity_check"]:
            if not out_dict["validity_check"][modname]:
                failed_plugins += [f"{intname} on {modname}"]
            else:
                successful_plugins += [f"{intname} on {modname}"]

    # Print all failed plugin tracebacks to interactive log level.
    for failed_plugins_traceback in failed_plugins_tracebacks:
        LOG.interactive(failed_plugins_traceback)
        LOG.interactive("")

    # Only include full list of successful plugins at LOG.info level, not interactive.
    for curr_plugin in successful_plugins:
        LOG.info(f"SUCCESSFUL PLUGIN {curr_plugin}")

    # Print successful interfaces to interactive log level.
    for curr_successful in successful_interfaces:
        LOG.interactive(f"SUCCESSFUL INTERFACE {curr_successful}")

    # Print failed plugins to interactive log level.
    for curr_failed in failed_plugins:
        LOG.interactive(f"FAILED PLUGIN IN {curr_failed}")

    # Print failed interfaces to interactive log level.
    for curr_failed in failed_interfaces:
        LOG.interactive(f"FAILED INTERFACE VALIDITY CHECK DICT {curr_failed}")

    # Print actual failed plugin errors to interactive log level.
    for failed_plugins_error in failed_plugins_errors:
        LOG.interactive(failed_plugins_error)
        LOG.interactive("")

    # Now, after reporting all errors individually, raise an exception if there were
    # any failed interfaces/plugins.  Include list of interfaces/plugins that had
    # failures within the exception string.
    if len(failed_interfaces) > 0 or len(failed_plugins) > 0:
        failed_plugin_headers = ""
        for failed_plugin in failed_plugins:
            failed_plugin_headers += (
                f"\n  {FAILED_INTERFACE_HEADER_PRE} '{failed_plugin}' "
                f"{FAILED_INTERFACE_HEADER_POST}"
            )
        raise TypeError(
            f"Failed validity check on interfaces {failed_plugins}."
            "\nAdditional information on these errors can be found above, "
            "under headers:"
            f"{failed_plugin_headers}"
        )


if __name__ == "__main__":
    main()
