# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Sector metadata generators interface class."""

from geoips.interfaces.class_based_plugin import BaseClassPlugin
from geoips.interfaces.base import BaseClassInterface


class BaseSectorMetadataGeneratorPlugin(BaseClassPlugin, abstract=True):
    """Base class for GeoIPS sector_metadata_generator plugins."""

    pass


class DeckSectorMetaGeneratorPlugin(BaseSectorMetadataGeneratorPlugin, abstract=True):
    """Base class for GeoIPS deck-based sector_metadata_generator plugins."""

    def assemble_invest_storm_id(
        self, storm_basin, invest_number, storm_year, storm_start_datetime
    ):
        """Assemble invest storm ID from basin, invest number, year, and start datetime.

        Of format bbNNyyyyYYYYMMDD, where

        * bb is the storm basin (lower case)
        * NN is the 2-digit invest number (9x)
        * yyyy is the storm year
        * YYYYMMDDHH is the storm start datetime.

        Note Invest storm ids include the storm start datetime, but numbered storm
        ids do not.

        * numbered storm bbNNyyyy
        * invest storm bbNNyyyyYYYYMMDDHH (ugly, but consistent with no delimiters)
        """
        return "%s%02d%04d%s" % (
            storm_basin.lower(),
            int(invest_number),
            int(storm_year),
            storm_start_datetime.strftime("%Y%m%d%H"),
        )

    def assemble_numbered_storm_id(self, storm_basin, storm_number, storm_year):
        """Assemble numbered storm ID from storm basin, number, and year.

        Of format bbNNyyyy, where

        * bb is the storm basin (lower case)
        * NN is the 2-digit invest number (9x)
        * yyyy is the storm year.

        Note Invest storm ids include the storm start datetime, but numbered storm
        ids do not.

        * numbered storm bbNNyyyy
        * invest storm bbNNyyyyYYYYMMDDHH (ugly, but consistent with no delimiters)
        """
        return "%s%02d%04d" % (
            storm_basin.lower(),
            int(storm_number),
            int(storm_year),
        )


class SectorMetadataGeneratorsInterface(BaseClassInterface):
    """Interface for generating appropriate metadata for a sector.

    Provides specification for generating a dictionary-based set of
    metadata that corresponds to a given sector.  The sector "family"
    determines the formatting and contents of the metadata dictionary.
    """

    name = "sector_metadata_generators"
    plugin_class = BaseSectorMetadataGeneratorPlugin

    required_args = {"tc": ["trackfile_name"], "volc": ["trackfile_name"]}
    required_kwargs = {"tc": [], "volc": []}


sector_metadata_generators = SectorMetadataGeneratorsInterface()
