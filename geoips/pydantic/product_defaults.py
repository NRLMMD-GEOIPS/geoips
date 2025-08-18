"""Pydantic PluginModel for GeoIPS product_default plugins.

Validates product_default plugins using pydantic. Intended to be a 'carryover' model
which will be used until we fully switch over to using workflow plugins.
"""

from typing import List  # , Literal, Tuple, Union

# from typing_extensions import Annotated

from pydantic import (
    Field,
    ConfigDict,
    model_validator,
)

from geoips.pydantic.bases import (
    FrozenModel,
    PermissiveFrozenModel,
    PythonIdentifier,
    PluginModel,
)


class ProductDefaultSpec(PermissiveFrozenModel):
    """Format to specify a product_default plugin model."""

    pass


class ProductDefaultPluginModel(PluginModel):
    """Format for product_default plugins.

    Validated with pydantic models.
    """

    model_config = ConfigDict(extra="allow")
    spec: ProductDefaultSpec = Field(
        ..., description="The specification of a product default plugin."
    )
