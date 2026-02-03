# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Gridline Annotator interface module."""

from geoips.interfaces.base import BaseYamlInterface
from geoips.pydantic_models.v1.gridline_annotators import GridlineAnnotatorPluginModel


class GridlineAnnotatorsInterface(BaseYamlInterface):
    """Interface for gridline annotator plugins."""

    name = "gridline_annotators"

    # Keyword arguments that can be used to adjust the style of lat/lon labels applied
    # to annotated imagery. See geoips.image_utils.maps:draw_gridlines for how this is
    # implemented
    label_kwargs = {
        "alpha": ["number"],
        "backgroundcolor": ["string"],
        "color": ["string"],
        "fontfamily": ["string"],
        "fontsize": ["number", "string"],
        "fontstretch": ["integer", "string"],
        "fontstyle": ["string"],
        "fontvariant": ["string"],
        "fontweight": ["integer", "string"],
        "linespacing": ["number"],
        "mouseover": ["boolean"],
        "position": ["array"],
        "rotation": ["number", "string"],
        "rotation_mode": ["string"],
        "snap": ["boolean"],
        "wrap": ["boolean"],
        "zorder": ["number"],
    }
    validator = GridlineAnnotatorPluginModel


gridline_annotators = GridlineAnnotatorsInterface()
