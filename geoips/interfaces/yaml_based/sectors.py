# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Sector interface module."""

from geoips.filenames.base_paths import PATHS as gpaths
from geoips.interfaces.base import BaseYamlInterface


class SectorsInterface(BaseYamlInterface):
    """Interface for sector plugins."""

    name = "sectors"
    use_pydantic = gpaths["GEOIPS_USE_PYDANTIC"]
    # if sectors.get_plugin(<name>) is found to be a dynamic sector. Otherwise, a static
    # sector plugin model (I.e. SectorPluginModel) will be used for all other sector
    # types.

    def _get_plugin_class(self):
        """Get the BaseSectorPlugin object for this interface.

        Returns
        -------
        BaseSectorPlugin
            The base class for all YAML sector plugins.
        """
        from geoips.interfaces.yaml_based.bases.sectors import BaseSectorPlugin

        return BaseSectorPlugin


sectors = SectorsInterface()
