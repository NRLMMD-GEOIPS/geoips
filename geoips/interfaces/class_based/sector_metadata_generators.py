# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Sector metadata generators interface class."""

from datetime import datetime
import logging
import os

from geoips.interfaces.class_based_plugin import BaseClassPlugin
from geoips.interfaces.base import BaseClassInterface

LOG = logging.getLogger(__name__)


class BaseSectorMetadataGeneratorPlugin(BaseClassPlugin, abstract=True):
    """Base class for GeoIPS sector_metadata_generator plugins."""

    data_tree = False

    pass


class DeckSectorMetaGeneratorPlugin(BaseSectorMetadataGeneratorPlugin, abstract=True):
    """Base class for GeoIPS deck-based sector_metadata_generator plugins."""

    def get_stormyear_from_filename(self, deck_filename):
        """Get the storm year from a deck filename.

        Parameters
        ----------
        deck_filename : str
            Path to deck file. Must be of format: xxxxxYYYY.*.dat

        Returns
        -------
        int
            Storm year
        """
        return int(os.path.basename(deck_filename)[5:9])

    def get_storm_start_datetime_from_filename(self, deck_filename):
        """Return the storm start time found in the actual filename, if it exists.

        Standard ATCF deck file names do NOT include the storm start datetime.

        Standard deck filenames

        * bsh912026.dat
        * bsh122026.dat

        Some processing systems will set the original storm start datetime
        when the very first position is received, then maintain that same value
        in the deck filenames throughout the life of the storm (invest and numbered).

        Enhanced filenames, including storm start datetime

        * bsh912026.2026010212.dat
        * bsh122026.2026010212.dat
        """
        deck_parts = os.path.basename(deck_filename).split(".")
        storm_start_datetime = None
        if len(deck_parts) > 2:
            try:
                storm_start_datetime = datetime.strptime(deck_parts[1], "%Y%m%d%H")
                LOG.info(
                    "  USING storm start time found in filename %s",
                    storm_start_datetime,
                )
            except ValueError:
                LOG.warning(
                    "  SKIPPING no valid storm start time found in filename, %s",
                    "using first entry in deck file",
                )
                storm_start_datetime = None
        return storm_start_datetime

    def lat_to_dec(self, lat_str):
        """Return decimal latitude based on N/S specified string."""
        latnodec = lat_str
        latdec = latnodec[:-2] + "." + latnodec[-2:]
        return latdec[:-1] if latdec[-1] == "N" else "-" + latdec[:-1]

    def lon_to_dec(self, lon_str):
        """Return decimal longitude based on E/W specified string."""
        lonnodec = lon_str
        londec = lonnodec[:-2] + "." + lonnodec[-2:]
        return londec[:-1] if londec[-1] == "E" else "-" + londec[:-1]

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
