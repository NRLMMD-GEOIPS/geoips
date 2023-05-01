"""Gridline Annotator interface module."""

from geoips.interfaces.base import BaseYamlInterface


class GridlineAnnotatorsInterface(BaseYamlInterface):
    """Interface for gridline annotator plugins."""

    name = "gridline_annotators"


gridline_annotators = GridlineAnnotatorsInterface()
