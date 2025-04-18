"""Pydantic models used to validate GeoIPS feature annotator plugins."""

from pydantic import Field

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
    edgecolor: ColorType = Field(
        None,
        description=(
            "A rgb tuple, matplotlib named color, or hexidecimal string (#XXXXXX) to "
            "apply to the edges of the cartopy feature.\n"
            "For more info, see: "
            "https://matplotlib.org/stable/users/explain/colors/colors.html"
        ),
    )
    # NOTE: Once we add land / ocean features, we'll need to add another field, labeled
    # facecolor.
    linewidth: float = Field(
        None, ge=0, description="The width in pixels of the specified feature."
    )


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
    background: ColorType = Field(
        None,
        description=(
            "A rgb tuple, matplotlib named color, or hexidecimal string (#XXXXXX) "
            "to apply to the background of your image.\n"
            "For more info, see: "
            "https://matplotlib.org/stable/users/explain/colors/colors.html"
        ),
    )


class FeatureAnnotatorPluginModel(PluginModel):
    """Feature Annotator plugin format."""

    spec: FeatureAnnotatorSpec = Field(
        ...,
        description=(
            "Specification of how to apply cartopy features to your annotated imagery. "
            "Works alongside matplotlib and cartopy to generate these features."
            "For more information, see: "
            "https://scitools.org.uk/cartopy/docs/v0.14/matplotlib/feature_interface.html"  # NOQAx
        ),
    )
