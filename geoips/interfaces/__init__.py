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

"""GeoIPS interface module."""

from geoips.interfaces.module_based.algorithms import algorithms
from geoips.interfaces.module_based.colormappers import colormappers
from geoips.interfaces.module_based.output_checkers import output_checkers
from geoips.interfaces.module_based.coverage_checkers import coverage_checkers
from geoips.interfaces.module_based.filename_formatters import filename_formatters
from geoips.interfaces.module_based.interpolators import interpolators
from geoips.interfaces.module_based.output_formatters import (
    output_formatters,
)
from geoips.interfaces.module_based.procflows import procflows
from geoips.interfaces.module_based.readers import readers
from geoips.interfaces.module_based.sector_adjusters import (
    sector_adjusters,
)
from geoips.interfaces.module_based.sector_metadata_generators import (
    sector_metadata_generators,
)
from geoips.interfaces.module_based.sector_spec_generators import (
    sector_spec_generators,
)
from geoips.interfaces.module_based.title_formatters import (
    title_formatters,
)

from geoips.interfaces.yaml_based.feature_annotators import (
    feature_annotators,
)
from geoips.interfaces.yaml_based.gridline_annotators import (
    gridline_annotators,
)
from geoips.interfaces.yaml_based.product_defaults import product_defaults
from geoips.interfaces.yaml_based.products import products
from geoips.interfaces.yaml_based.sectors import sectors

# These lists are the "master" lists of the interface names.
# These are used in validating the plugins (ie, so we will catch a typo
# in an interface name)
module_based_interfaces = [
    "algorithms",
    "colormappers",
    "coverage_checkers",
    "filename_formatters",
    "interpolators",
    "output_checkers",
    "output_formatters",
    "procflows",
    "readers",
    "sector_adjusters",
    "sector_metadata_generators",
    "sector_spec_generators",
    "title_formatters",
]
yaml_based_interfaces = [
    "feature_annotators",
    "gridline_annotators",
    "product_defaults",
    "products",
    "sectors",
]
__all__ = module_based_interfaces + yaml_based_interfaces


def list_available_interfaces():
    """Collect and return every available interface for each interface 'family'."""
    import inspect
    from geoips import interfaces

    all_interfaces = {
        "module_based": [],
        "text_based": [],
        "yaml_based": [],
    }
    for interface_type in ["module", "text", "yaml"]:
        try:
            available_interfaces = [
                str(mod_info[0])
                for mod_info in inspect.getmembers(
                    getattr(interfaces, f"{interface_type}_based"),
                    inspect.ismodule,
                )
            ]
            all_interfaces[f"{interface_type}_based"] = available_interfaces
        except AttributeError:
            continue

    return all_interfaces
