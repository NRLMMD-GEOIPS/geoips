# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Sector metadata generators interface module."""

from geoips.interfaces.base import BaseModuleInterface


class SectorMetadataGeneratorsInterface(BaseModuleInterface):
    """Interface for generating appropriate metadata for a sector.

    Provides specification for generating a dictionary-based set of
    metadata that corresponds to a given sector.  The sector "family"
    determines the formatting and contents of the metadata dictionary.
    """

    name = "sector_metadata_generators"
    required_args = {"tc": ["trackfile_name"]}
    required_kwargs = {"tc": []}


sector_metadata_generators = SectorMetadataGeneratorsInterface()
