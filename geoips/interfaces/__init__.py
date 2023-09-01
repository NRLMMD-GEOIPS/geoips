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
from geoips.interfaces.module_based.coverage_checkers import coverage_checkers
from geoips.interfaces.module_based.filename_formatters import filename_formatters
from geoips.interfaces.module_based.interpolators import interpolators
from geoips.interfaces.module_based.output_formatters import output_formatters
from geoips.interfaces.module_based.procflows import procflows
from geoips.interfaces.module_based.readers import readers
from geoips.interfaces.module_based.sector_adjusters import sector_adjusters
from geoips.interfaces.module_based.sector_metadata_generators import (
    sector_metadata_generators,
)
from geoips.interfaces.module_based.sector_spec_generators import sector_spec_generators
from geoips.interfaces.module_based.title_formatters import title_formatters

from geoips.interfaces.yaml_based.feature_annotators import feature_annotators
from geoips.interfaces.yaml_based.gridline_annotators import gridline_annotators
from geoips.interfaces.yaml_based.product_defaults import product_defaults
from geoips.interfaces.yaml_based.products import products
from geoips.interfaces.yaml_based.sectors import sectors

__all__ = [
    "algorithms",
    "colormappers",
    "coverage_checkers",
    "feature_annotators",
    "filename_formatters",
    "gridline_annotators",
    "interpolators",
    "output_formatters",
    "procflows",
    "product_defaults",
    "products",
    "readers",
    "sector_adjusters",
    "sector_metadata_generators",
    "sector_spec_generators",
    "sectors",
    "title_formatters",
]
