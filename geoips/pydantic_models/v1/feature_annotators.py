# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Pydantic models used to validate GeoIPS feature annotator plugins."""

from pydantic import Field, model_validator
from typing import Optional

from geoips.pydantic_models.v1.bases import (
    FrozenModel,
    PermissiveFrozenModel,
    PluginModel,
    ColorType,
)

MATPLOTLIB_COLOR_DOC = (
    "An rgb tuple, matplotlib named color, or hexidecimal string (#XXXXXX)."
    "For more info, see: "
    "https://matplotlib.org/stable/users/explain/colors/colors.html"
)


class CartopyFeature(PermissiveFrozenModel):
    """Generic model for cartopy features."""

    enabled: bool = Field(
        ..., strict=True, description="Whether or not to enable this feature."
    )
    edgecolor: ColorType = Field(
        None, description=f"{MATPLOTLIB_COLOR_DOC} Used for Cartopy feature edges."
    )
    # NOTE: Once we add land / ocean features, we'll need to add another field, labeled
    # facecolor.
    linewidth: Optional[float] = Field(
        None, ge=0, description="The width in pixels of the specified feature."
    )
    # TODO: There are more arguments here for a mpl Line2D artist and cartopy features.
    # do we want to support all of those? Do we want to fail before or let
    # matplotlib fail

    @model_validator(mode="after")
    def validate_enabled_fields(cls, values):
        """Validate edgecolor and linewidth based on the value of 'enabled'.

        If enabled is True, then both edgecolor and linewidth must be provided.
        """
        enabled = values.enabled
        edgecolor = values.edgecolor
        linewidth = values.linewidth

        if enabled:
            if edgecolor is None or linewidth is None:
                raise ValueError(
                    "If 'enabled' is True, both 'edgecolor' and 'linewidth' must be "
                    "provided."
                )

        return values


class FeatureAnnotatorSpec(FrozenModel):
    """Feature Annotator spec (specification) format."""

    # NOTE: Will need to add land and ocean features once they've been merged into main.
    coastline: CartopyFeature = Field(
        ..., strict=True, description="A cartopy coastline feature."
    )
    borders: CartopyFeature = Field(
        ..., strict=True, description="A cartopy borders feature."
    )
    rivers: CartopyFeature = Field(
        ..., strict=True, description="A cartopy rivers feature."
    )
    states: CartopyFeature = Field(
        ..., strict=True, description="A cartopy states feature."
    )
    background: Optional[ColorType] = Field(
        None,
        description=f"{MATPLOTLIB_COLOR_DOC} used for the background of the image.",
    )


class FeatureAnnotatorPluginModel(PluginModel):
    """Feature Annotator plugin format."""

    spec: FeatureAnnotatorSpec = Field(
        ...,
        description=(
            "Specification of how to apply cartopy features to your annotated imagery. "
            "Works alongside matplotlib and cartopy to generate these features. "
            "For more information, see: "
            "https://scitools.org.uk/cartopy/docs/v0.14/matplotlib/feature_interface.html"  # noqa : E501
        ),
    )


# TODO: load a model, parse the model to look at all its fields, collect all of the
# arguments for the matplotlib artist, compare arguments to make sure nothing differs
