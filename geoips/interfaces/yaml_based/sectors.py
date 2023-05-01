"""Sector interface module."""

from geoips.interfaces.base import BaseYamlInterface


class SectorsInterface(BaseYamlInterface):
    """Interface for sector plugins."""

    name = "sectors"


sectors = SectorsInterface()
