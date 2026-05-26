# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Pydantic models used to validate GeoIPS OBP v1 colormapper plugins."""

# Python Standard Libraries
from typing import List

# Third-Party Libraries
from pydantic import Field

# GeoIPS imports
from geoips.pydantic_models.v1.bases import PermissiveFrozenModel


class ColormapperArgumentsModel(PermissiveFrozenModel):
    """Colormapper step argument definition.

    Pydantic model defining and validating Colormapper step arguments.
    """

    cbar_label: str = Field(
        None,
        description=(
            "Positional parameter passed to cbar.set_label"
            " If specified, use cbar_label string as colorbar label."
        ),
    )
    cbar_ticks: tuple[float] = Field(
        None,
        description=(
            "Positional parameter passed to cbar.set_ticks"
            " Specify explicit list of ticks to include for colorbar."
            "None indicates ticks at int(min) and int(max) values"
        ),
    )
    cmap_name: str = Field(
        "Greys",
        description=(
            "Specify the name of the resulting matplotlib colormap. If no ascii_path"
            " specified, will use builtin matplotlib colormap of name cmap_name."
        ),
    )
    create_colorbar: bool = Field(
        True, description="Specify whether the image should contain a colorbar or not."
    )
    pressure_range_legend: List[str] = Field(
        None,
        description="List of strings that are used for setting the cbar tick labels",
    )
