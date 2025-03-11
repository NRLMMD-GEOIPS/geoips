# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Simple test script to run "test_interface" for each interface."""
from pprint import pformat
import traceback
import json

from geoips import interfaces
from geoips.interfaces.base import BaseInterface
from geoips.commandline.log_setup import setup_logging
from geoips.commandline.args import get_argparser, check_command_line_args
from geoips.utils.context_managers import import_optional_dependencies

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
    failed_registries = []

    successful_interfaces = []
    successful_plugins = []
    successful_registries = []

    failed_errors = []
    failed_tracebacks = []

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

    # Plugin registry was previously being tested during runtime.
    # We want to avoid catastrophic failure at runtime for a single
    # bad plugin, so ensure these are validated in testing, and allow
    # bad plugins to get through at runtime.

    # NOTE: The section below will only be used if the user has pytest installed. We
    # still should figure out where and when we'd like to validate the plugin
    # registries. Currently validation of the registires invokes pytest, which is not a
    # required dependency of GeoIPS. Calls 'plg_reg.validate_all_registries()' and
    # 'plg_reg.validate_registry(pkg_plugins, reg_path)' are no longer on the plugin
    # registry class, rather, they can be found under
    # 'geoips/tests/unit_tests/plugin_registries/test_plugin_registries.py' -->
    # PluginRegistryValidator

    with import_optional_dependencies(loglevel="interactive"):
        """Attempt to import the pytest-based PluginRegistryValidator.

        If this import works, validate the registries for testing purposes. See
        'tests.unit_tests.plugin_registries.test_plugin_registries' for more
        information.
        """
        from tests.unit_tests.plugin_registries.test_plugin_registries import (
            PluginRegistryValidator,
        )
        from geoips.errors import PluginRegistryError

        plg_reg = PluginRegistryValidator()
        try:
            LOG.interactive("Testing all registries...")
            plg_reg.validate_all_registries()
            successful_registries += ["all"]
        except PluginRegistryError as resp:
            failed_registries += ["all"]
            failed_tracebacks += [
                f"\n\n\n{FAILED_INTERFACE_HEADER_PRE}\n\n{traceback.format_exc()}"
            ]
            failed_errors += [f"\n\n\n{FAILED_INTERFACE_HEADER_PRE}\n\n {str(resp)}"]

        # Now test each registry file individually.
        for reg_path in plg_reg.registry_files:
            pkg_plugins = json.load(open(reg_path, "r"))
            LOG.interactive(f"Testing registry: {reg_path}...")
            try:
                plg_reg.validate_registry(pkg_plugins, reg_path)
                successful_registries += [reg_path]
            except PluginRegistryError as resp:
                failed_registries += [reg_path]
                failed_tracebacks += [
                    f"\n\n\n{FAILED_INTERFACE_HEADER_PRE} '{reg_path}'\n\n"
                    f"{traceback.format_exc()}"
                ]
                failed_errors += [
                    f"\n\n\n{FAILED_INTERFACE_HEADER_PRE} '{reg_path}'\n\n{str(resp)}"
                ]

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
            failed_tracebacks += [
                f"\n\n\n{FAILED_INTERFACE_HEADER_PRE} '{curr_interface.name}' "
                f"{FAILED_INTERFACE_HEADER_POST}\n\n"
                f"{traceback.format_exc()}"
            ]
            failed_errors += [
                f"\n\n\n{FAILED_INTERFACE_HEADER_PRE} '{curr_interface.name}' "
                f"{FAILED_INTERFACE_HEADER_POST}\n\n"
                f"{str(resp)}"
            ]

    # Collect lists of the successful and failed plugins (without actual errors)
    for intname in out_dicts:
        LOG.info("%s", pformat(out_dict))
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
    for failed_traceback in failed_tracebacks:
        LOG.interactive(failed_traceback)
        LOG.interactive("")

    # Only include full list of successful plugins at LOG.info level, not interactive.
    for curr_plugin in successful_plugins:
        LOG.info(f"SUCCESSFUL PLUGIN {curr_plugin}")

    # Print successful registries to interactive log level.
    for curr_successful in successful_registries:
        LOG.interactive(f"SUCCESSFUL REGISTRY {curr_successful}")

    # Print successful interfaces to interactive log level.
    for curr_successful in successful_interfaces:
        LOG.interactive(f"SUCCESSFUL INTERFACE {curr_successful}")

    # Print failed plugins to interactive log level.
    for curr_failed in failed_plugins:
        LOG.interactive(f"FAILED PLUGIN IN {curr_failed}")

    # Print failed registries to interactive log level.
    for curr_failed in failed_registries:
        LOG.interactive(f"FAILED REGISTRY IN {curr_failed}")

    # Print failed interfaces to interactive log level.
    for curr_failed in failed_interfaces:
        LOG.interactive(f"FAILED INTERFACE VALIDITY CHECK DICT {curr_failed}")

    # Print actual failed plugin errors to interactive log level.
    for failed_error in failed_errors:
        LOG.interactive(failed_error)
        LOG.interactive("")

    # Now, after reporting all errors individually, raise an exception if there were
    # any failed interfaces/plugins.  Include list of interfaces/plugins that had
    # failures within the exception string.
    if (
        len(failed_interfaces) > 0
        or len(failed_plugins) > 0
        or len(failed_registries) > 0
    ):
        failed_headers = ""
        for failed_plugin in failed_plugins:
            failed_headers += (
                f"\n  {FAILED_INTERFACE_HEADER_PRE} '{failed_plugin}' "
                f"{FAILED_INTERFACE_HEADER_POST}"
            )
        for failed_registry in failed_registries:
            failed_headers += f"\n  {FAILED_INTERFACE_HEADER_PRE} '{failed_registry}' "
        raise TypeError(
            f"Failed validity checks on registries:\n"
            f"{pformat(failed_registries)}.\n"
            f"Failed validity checks on plugins:\n"
            f"{pformat(failed_plugins)}.\n"
            "\nAdditional information on these errors can be found above, "
            "under headers:\n"
            f"{failed_headers}"
        )


if __name__ == "__main__":
    main()
