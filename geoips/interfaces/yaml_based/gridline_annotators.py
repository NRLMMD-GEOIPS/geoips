# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Gridline Annotator interface module."""

from geoips.interfaces.base import BaseYamlInterface


class GridlineAnnotatorsInterface(BaseYamlInterface):
    """Interface for gridline annotator plugins."""

    name = "gridline_annotators"


gridline_annotators = GridlineAnnotatorsInterface()
