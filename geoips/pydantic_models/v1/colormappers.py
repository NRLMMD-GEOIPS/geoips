# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Pydantic models used to validate GeoIPS OBP v1 colormapper plugins."""

# Python Standard Libraries
from typing import List

# Third-Party Libraries
from pydantic import Field

# GeoIPS imports
from geoips.pydantic_models.v1.bases import PermissiveFrozenModel

PLUGIN_PROVIDED = "plugin_provided"


class ColormapperArgumentsModel(PermissiveFrozenModel):
    """Colormapper step argument definition.

    Pydantic model defining and validating Colormapper step arguments.
    """

    cbar_full_width: bool = Field(
        default=False,
        description='"Extend the colorbar across the full width of the image"',
    )
    cbar_label: str = Field(
        default=PLUGIN_PROVIDED,
        description=(
            "Positional parameter passed to cbar.set_label"
            " If specified, use cbar_label string as colorbar label."
        ),
    )
    cbar_spacing: str = Field(
        "proportional",
        description=(
            '"spacing" argument to pass to fig.colorbar;'
            ' can also specify directly within "colorbar_kwargs"'
        ),
    )
    cbar_ticks: list[float] | None = Field(
        None,
        description=(
            "Positional parameter passed to cbar.set_ticks"
            " Specify explicit list of ticks to include for colorbar."
            "None indicates ticks at int(min) and int(max) values"
        ),
    )
    cbar_tick_labels: list[str] | None = Field(
        None,
        description=(
            "'labels' argument to pass to cbar.set_ticks."
            " can also specify directly within 'set_ticks_kwarg'"
        ),
    )
    cmap_name: str = Field(
        default=PLUGIN_PROVIDED,
        description=(
            "Specify the name of the resulting matplotlib colormap. If no ascii_path"
            " specified, will use builtin matplotlib colormap of name cmap_name."
        ),
    )
    cmap_path: str | None = Field(None)
    cmap_source: str = Field(default=PLUGIN_PROVIDED)

    colorbar_kwargs: dict | None = Field(
        None, description="keyword arguments to pass through directly to 'fig.colorbar'"
    )
    create_colorbar: bool | None = Field(
        True, description="Specify whether the image should contain a colorbar or not."
    )
    data_range: tuple[float, float] | str = Field(
        default=PLUGIN_PROVIDED,
        description=(
            "Min and max value for colormap"
            "matplotlib.colors.Normalize(vmin=min_val, vmax=max_val)"
        ),
    )
    pressure_range_legend: List[str] | None = Field(
        None,
        description="List of strings that are used for setting the cbar tick labels",
    )
    set_ticks_kwargs: dict | None = Field(
        None,
        description='keyword arguments to pass through directly to "cbar.set_ticks"',
    )
    set_label_kwarg: dict | None = Field(
        None,
        description='keyword arguments to pass through directly to "cbar.set_label"',
    )
