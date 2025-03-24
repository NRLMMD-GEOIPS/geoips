"""Pydantic models used to validate GeoIPS feature annotator plugins."""

from pydantic import Field, model_validator
from typing import Optional

from geoips.pydantic.bases import (
    FrozenModel,
    PermissiveFrozenModel,
    PluginModel,
    ColorType,
)


class CartopyFeature(PermissiveFrozenModel):
    """Generic model for cartopy features."""

    enabled: bool = Field(
        ..., strict=True, description="Whether or not to enable this feature."
    )
    edgecolor: Optional[ColorType] = Field(
        None,
        description=(
            "A rgb tuple, named color, or hexidecimal string to apply to the edges of "
            "the cartopy feature."
        ),
    )
    # NOTE: Once we add land / ocean features, we'll need to add another field, labeled
    # facecolor.
    linewidth: Optional[float] = Field(
        None, ge=0, description="The width in pixels of the specified feature."
    )

    @model_validator(mode="after")
    def validate_enabled_fields(cls, values):
        """Validate edgecolor and linewidth based on the value of 'enabled'.

        If enabled is True, then both edgecolor and linewidth must be provided.
        If set to False, then make sure that both edgecolor and linewidth are absent.
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
        else:
            if edgecolor is not None or linewidth is not None:
                raise ValueError(
                    "If 'enabled' is False, 'edgecolor' and 'linewidth' must not be "
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
        description=(
            "A rgb tuple, named color, or hexidecimal string to apply to the background"
            " of your image."
        ),
    )


class FeatureAnnotatorPluginModel(PluginModel):
    """Feature Annotator plugin format."""

    spec: FeatureAnnotatorSpec = Field(
        ...,
        description=(
            "Specification of how to apply features to your annotated imagery. "
            "Works alongside matplotlib and cartopy to generate these features."
        ),
    )
