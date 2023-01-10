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

"""Simple script to list available modules for each interface.

This includes both dev and stable interfaces.
Note this will be deprecated with v2.0, replaced with a new class-based
interface implementation.
"""
import pprint
from importlib import import_module
import traceback
import warnings

# Always actually raise DeprecationWarnings
# Note this SO answer https://stackoverflow.com/a/20960427
warnings.simplefilter("always", DeprecationWarning)


def main():
    """Script to list all modules available in the current geoips instantiation."""
    interfaces = {
        "stable.reader": "list_readers_by_type",
        "dev.alg": "list_algs_by_type",
        "dev.boundaries": "list_boundaries_by_type",
        "dev.cmap": "list_cmaps_by_type",
        "dev.filename": "list_filenamers_by_type",
        "dev.gridlines": "list_gridlines_by_type",
        "dev.interp": "list_interps_by_type",
        "dev.output": "list_outputters_by_type",
        "dev.procflow": "list_procflows_by_type",
        "dev.product": "list_products_by_type",
    }

    for curr_interface, list_func in interfaces.items():
        print("")
        test_curr_interface = getattr(
            import_module(f"geoips.{curr_interface}"), f"{list_func}"
        )
        try:
            out_dict = test_curr_interface()
        except Exception:
            print(traceback.format_exc())
            raise

        print(f"Available {curr_interface} modules:")

        ppprinter = pprint.PrettyPrinter(indent=2)
        ppprinter.pprint(dict(out_dict))


if __name__ == "__main__":
    main()
