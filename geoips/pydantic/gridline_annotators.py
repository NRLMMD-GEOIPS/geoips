"""Pydantic models used to validate GeoIPS gridline annotator plugins."""

from pydantic import Field
from typing import Union, List, Optional

from geoips.pydantic.bases import (
    FrozenModel,
    PermissiveFrozenModel,
    PluginModel,
    ColorType,
)


class Spacing(FrozenModel):
    """Model used to format the spacing of gridlines in annotated imagery."""

    latitude: Union[float, str] = Field(
        ..., description="Latitude spacing value, can be a number or a string."
    )
    longitude: Union[float, str] = Field(
        ..., description="Longitude spacing value, can be a number or a string."
    )


class Labels(PermissiveFrozenModel):
    """Model used to format labels in annotated imagery."""

    top: bool = Field(..., description="Whether to display the label at the top.")
    bottom: bool = Field(..., description="Whether to display the label at the bottom.")
    left: bool = Field(..., description="Whether to display the label on the left.")
    right: bool = Field(..., description="Whether to display the label on the right.")
    alpha: Optional[float] = Field(
        None,
        description=(
            "Inverse percentage of label transparency (0 = fully transparent, 1 = fully"
            "opaque)."
        ),
    )
    backgroundcolor: Optional[str] = Field(
        None,
        description="Background color of the label frame (matplotlib color or hex).",
    )
    color: Optional[str] = Field(
        None, description="Color of the label text (matplotlib color or hex)."
    )
    fontfamily: Optional[str] = Field(
        None, description="Font family for the label text."
    )
    fontsize: Optional[Union[float, str]] = Field(
        None, description="Font size for the label text."
    )
    fontstretch: Optional[Union[int, str]] = Field(
        None, description="Stretch level of the font."
    )
    fontstyle: Optional[str] = Field(
        None, description="Style of the font (e.g., 'normal', 'italic', 'oblique')."
    )
    fontvariant: Optional[str] = Field(
        None, description="Font variant (e.g., 'normal', 'small-caps')."
    )
    fontweight: Optional[Union[int, str]] = Field(
        None, description="Weight of the font."
    )
    linespacing: Optional[float] = Field(
        None, description="Spacing between lines of text."
    )
    mouseover: Optional[bool] = Field(
        None, description="Whether to enable mouseover effect."
    )
    position: Optional[List[float]] = Field(
        None, description="Absolute (x, y) position of the label."
    )
    rotation: Optional[Union[float, str]] = Field(
        None, description="Rotation of the label (degrees or 'vertical'/'horizontal')."
    )
    rotation_mode: Optional[str] = Field(
        None, description="Rotation mode ('default' or 'anchor')."
    )
    snap: Optional[bool] = Field(
        None, description="Whether to snap the label to the pixel grid."
    )
    wrap: Optional[bool] = Field(None, description="Whether to allow text wrapping.")
    zorder: Optional[float] = Field(
        None, description="Order of label rendering (lower value = earlier rendering)."
    )
    xpadding: Optional[int] = Field(None, description="Pixel offset for x-axis labels.")
    ypadding: Optional[int] = Field(None, description="Pixel offset for y-axis labels.")


class Lines(FrozenModel):
    """Model used to format gridlines in annotated imagery."""

    color: str = Field(..., description="Color of the line.")
    linestyle: List[int] = Field(
        ...,
        min_items=2,
        max_items=2,
        description="Pattern of dashes and gaps in the line.",
    )
    linewidth: float = Field(..., description="Width of the line.")


class GridlineAnnotatorSpec(FrozenModel):
    """Gridline Annotator spec (specification) format."""

    spacing: Spacing = Field(..., description="Spacing settings for the plot.")
    labels: Labels = Field(..., description="Label settings for the plot.")
    lines: Lines = Field(..., description="Line settings for the plot.")
    background: Optional[ColorType] = Field(
        None,
        description=(
            "A rgb tuple, named color, or hexidecimal string to apply to the background"
            " of your image frame."
        ),
    )


class GridlineAnnotatorPluginModel(PluginModel):
    """Gridline Annotator plugin format."""

    spec: GridlineAnnotatorSpec = Field(
        ...,
        description=(
            "Specification of how to apply gridlines, labels, and spacing to your "
            "annotated imagery. Works alongside matplotlib and cartopy to generate "
            "these attributes."
        ),
    )
