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

    data_range: tuple[float, float] = Field(
        Plugin_provided, description="Min and max value for colormap"
    )
    cbal_lavel: str = Field(Plugin_provided, description="")
    pressure_range_legend: List[str] = Field(
        None,
        description="List of strings that are used for setting the cbar tick labels",
    )
    data_range = (None,)
    cmap_name = ("Greys",)
    cmap_source = ("matplotlib",)
    cmap_path = (None,)
    create_colorbar = (True,)
    cbar_label = (None,)
    cbar_ticks = (None,)
    cbar_tick_labels = (None,)
    cbar_spacing: str = Field(
        "proportional",
        description='"spacing" argument to pass to fig.colorbar; can also specify directly within "colorbar_kwargs"',
    )
    cbar_full_width: bool = Field(
        True, description='"Extend the colorbar across the full width of the image"'
    )
    colorbar_kwargs: dict = Field(
        None, description='keyword arguments to pass through directly to "fig.colorbar"'
    )
    set_ticks_kwargs: dict = Field(
        None,
        description='keyword arguments to pass through directly to "cbar.set_ticks"',
    )
    set_label_kwarg: dict = Field(
        None,
        description='keyword arguments to pass through directly to "cbar.set_label"',
    )
