"""Pydantic models used to validate GeoIPS gridline annotator plugins."""

from typing import Literal, Union, List, Optional

from pydantic import Field

from geoips.models.v1.bases import (
    FrozenModel,
    PermissiveFrozenModel,
    PluginModel,
    ColorType,
)


class Spacing(FrozenModel):
    """Model used to format the spacing of gridlines in annotated imagery."""

    latitude: Union[float, Literal["auto"]] = Field(
        ...,
        description=(
            "Latitude spacing in degrees, can be a float or a string. If a string, it "
            "must be 'auto', which represents automatic spacing based on your area_def."
        ),
    )
    longitude: Union[float, Literal["auto"]] = Field(
        ...,
        description=(
            "Longitude spacing in degrees, can be a float or a string. If a string, it "
            "must be 'auto', which represents automatic spacing based on your area_def."
        ),
    )


class Labels(PermissiveFrozenModel):
    """Model used to format labels in annotated imagery.

    For more information, visit https://matplotlib.org/stable/ to see more context in
    how to specify these fields.
    """

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
    backgroundcolor: Optional[ColorType] = Field(
        None,
        description=(
            "A rgb tuple, matplotlib named color, or hexidecimal string (#XXXXXX) "
            "to apply to the background of your label frame.\n"
            "For more info, see: "
            "https://matplotlib.org/stable/users/explain/colors/colors.html"
        ),
    )
    color: Optional[ColorType] = Field(
        None,
        description=(
            "A rgb tuple, matplotlib named color, or hexidecimal string (#XXXXXX) "
            "to apply to the label text of your image.\n"
            "For more info, see: "
            "https://matplotlib.org/stable/users/explain/colors/colors.html"
        ),
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
    """Model used to format gridlines in annotated imagery.

    For more information, visit https://matplotlib.org/stable/ to see more context in
    how to specify these fields.
    """

    color: ColorType = Field(
        ..., description="Color of the line (named color, hex, or rgb tuple)."
    )
    linestyle: List[int] = Field(
        ...,
        min_items=2,
        max_items=2,
        description="Pattern of dashes and gaps in the line.",
    )
    linewidth: float = Field(..., description="Width of the line.")
    # TODO: create file called matplotlib or 'artists', which contains all the machinery
    # that relates with this


class GridlineAnnotatorSpec(FrozenModel):
    """Gridline Annotator spec (specification) format."""

    spacing: Spacing = Field(..., description="Spacing settings for the plot.")
    labels: Labels = Field(..., description="Label settings for the plot.")
    lines: Lines = Field(..., description="Line settings for the plot.")
    background: Optional[ColorType] = Field(
        None,
        description=(
            "A rgb tuple, matplotlib named color, or hexidecimal string (#XXXXXX) "
            "to apply to the background of your image frame.\n"
            "For more info, see: "
            "https://matplotlib.org/stable/users/explain/colors/colors.html"
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
