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

"""Simple test script to run "test_<interface>_interface" for each interface.

This includes both dev and stable interfaces.
Note this will be deprecated with v2.0 - replaced with a new class-based
interface implementation.
"""
import pprint
import traceback
from geoips import interfaces
from geoips.interfaces.base import BaseInterface
import sys


def main():
    """Script to test all dev and stable interfaces."""
    failed_interfaces = []
    failed_plugins = []
    successful_interfaces = []
    successful_plugins = []
    failed_plugins_errors = []
    failed_plugins_tracebacks = []

    curr_interfaces = interfaces.__dict__.values()
    if len(sys.argv) > 1:
        curr_interfaces = []
        for curr_interface in sys.argv[1:]:
            curr_interfaces += [interfaces.__dict__[curr_interface]]

    out_dicts = {}

    for curr_interface in curr_interfaces:
        if (type(curr_interface) is BaseInterface) or not isinstance(
            curr_interface, BaseInterface
        ):
            continue

        print("")
        print(f"Testing {curr_interface.name}...")

        # Open all the interfaces (not just checking call signatures)
        # This returns a dictionary of all sorts of stuff.
        try:
            out_dict = curr_interface.test_interface()
            out_dicts[curr_interface.name] = out_dict
        except Exception as resp:
            print(traceback.format_exc())
            failed_plugins += [curr_interface.name]
            failed_plugins_tracebacks += [
                f"Failed: {curr_interface.name}\n\n" f"{traceback.format_exc()}"
            ]
            failed_plugins_errors += [
                f"Failed: {curr_interface.name}\n\n" f"{str(resp)}"
            ]

    ppprinter = pprint.PrettyPrinter(indent=2)

    for intname in out_dicts:
        ppprinter.pprint(out_dict)
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

    for failed_plugins_traceback in failed_plugins_tracebacks:
        print(failed_plugins_traceback)
        print("")

    for curr_plugin in successful_plugins:
        print(f"SUCCESSFUL PLUGIN {curr_plugin}")

    for curr_successful in successful_interfaces:
        print(f"SUCCESSFUL INTERFACE {curr_successful}")

    for curr_failed in failed_plugins:
        print(f"FAILED PLUGIN {curr_failed}")

    for curr_failed in failed_interfaces:
        print(f"FAILED INTERFACE {curr_failed}")

    for failed_plugins_error in failed_plugins_errors:
        print(failed_plugins_error)
        print("")

    if len(failed_interfaces) > 0 or len(failed_plugins) > 0:
        raise TypeError(f"Failed validity check on plugins {failed_plugins}")


if __name__ == "__main__":
    main()
