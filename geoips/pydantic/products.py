"""Pydantic PluginModel for GeoIPS Product plugins.

Validates Product plugins using pydantic. Intended to be a 'carryover' model which will
be used until we fully switch over to using workflow plugins.
"""

from typing import List  # , Literal, Tuple, Union

# from typing_extensions import Annotated

from pydantic import (
    Field,
    ConfigDict,
    model_validator,
)
import yaml

from geoips.interfaces import product_defaults
from geoips.pydantic.bases import (
    FrozenModel,
    PermissiveFrozenModel,
    PythonIdentifier,
    PluginModel,
)
from geoips.pydantic.product_defaults import ProductDefaultPluginModel


FAMILIES_CHECKED_AGAINST = [
    "algorithm_colormapper",
    "algorithm_interpolator_colormapper",
    "algorithm",
    "interpolator_algorithm_colormapper",
    "interpolator_algorithm",
    "interpolator",
]


class AlgorithmColormapperInterpolatorModel(PermissiveFrozenModel):
    """Format specifying which plugin to use and the arguments to provide to it."""

    name: PythonIdentifier = Field(
        ..., description="The name of the plugin to be used."
    )
    arguments: dict = Field(
        ...,
        description=(
            "A dictionary of arbitrary arguments applicable to this specific plugin."
        ),
    )


class SpecPlugin(FrozenModel):
    """Simple model containing the name of the plugin and the arguments to feed it."""

    plugin: AlgorithmColormapperInterpolatorModel = Field(
        ...,
        desciption=(
            "The specification of the plugin being overridden or implemented directly. "
            "Should be one of the any of the following types of plugins:\n"
            "Algorithms, Colormappers, Interpolators"
        ),
    )


class ProductSpec(PermissiveFrozenModel):
    """Format of the argument specifications for a product plugin.

    Additional fields may be added as you can override a product_defaults' arguments if
    referenced. This may change in the future as we solidify what these arguments will
    look like.
    """

    variables: List[str] = Field(
        ...,
        description=(
            "A list of one or morevariables derived from one of the 'source_names' "
            "referenced in the product plugin. For example, 'B13BT' from 'abi' or "
            "'ahi'."
        ),
    )
    algorithm: SpecPlugin = Field(
        None, description="The specification of an algorithm plugin."
    )
    colormapper: SpecPlugin = Field(
        None, description="The specification of an colormapper plugin."
    )
    interpolator: SpecPlugin = Field(
        None, description="The specification of an interpolator plugin."
    )


class Product(FrozenModel):
    """Format for how to specify a singular product in a product plugin.

    Additional fields may not be added.
    """

    name: str = Field(
        ...,
        description=(
            "The name of the product being specified. Currently doesn't have to be a "
            "valid python identifier as we have some products (such as 89H) which don't"
            " adhere to that."
        ),
    )
    source_names: List[str] = Field(
        ...,
        description=(
            "A list of strings representing the source(s) this product is derived from."
            "Currently doesn't have to be a valid python identifier as we have some "
            "cases that don't adhere to that (such as amsu-a_mhs)."
        ),
    )
    docstring: str = Field(
        ...,
        description="A single or multiline description of what this product implements.",
    )
    family: PythonIdentifier = Field(
        None,
        description=(
            "The family this product falls under. Will be deprecated once the order "
            "based procflow has been implemented. Cannot be specified along the "
            "'product_defaults' field."
        ),
    )
    product_defaults: ProductDefaultPluginModel = Field(
        None,
        description=(
            "The name of the product_default plugin this product inherits from. "
            "Doesn't need to be a valid python identifier at the current time. Cannot "
            "be specified alongside the 'family' field."
        ),
    )
    spec: ProductSpec = Field(
        ...,
        description=(
            "The specification of specific arguments for this product plugin. "
            "Additionally, can override arguments specified in the product_defaults "
            "plugin it referenced if applicable."
        ),
    )

    # This runs first
    @model_validator(mode="after")
    def check_family_pd_xor(self):
        """Validate that either family or product_defaults is provided xor fashion.

        Meaning, only one of those options can be provided, not both or none.
        """
        if (self.family is None and self.product_defaults is None) or (
            self.family is not None and self.product_defaults is not None
        ):
            raise ValueError(
                "You must provide exactly one of 'family' or 'product_defaults'."
            )
        return self

    # This runs second
    @model_validator(mode="after")
    def load_product_default(self):
        """If a product_defaults entry has been provided, load it."""
        if self.product_defaults:
            abspath = product_defaults.get_plugin(self.product_defaults)["abspath"]
            yam = yaml.safe_load(open(abspath, "r"))
            self.product_defaults = ProductDefaultPluginModel(**yam)

        return self

    # This runs third
    @model_validator(mode="after")
    def validate_plugins_if_exist(self):
        """Validate that if a plugin is provided, it is part of the family provided.

        Where family comes from spec.family or spec.product_defaults.family.
        """
        if self.family:
            family_name = self.spec.family
        elif self.product_defaults.family:
            family_name = self.spec.family

        if family_name in FAMILIES_CHECKED_AGAINST:
            # Only validating for the alg-cmap-int -based families currently
            for plugin_type in ["algorithm", "colormapper", "interpolator"]:
                if hasattr(self.spec, plugin_type):
                    if plugin_type not in family_name:
                        raise ValueError(
                            f"Error: '{plugin_type}' plugin supplied but that does not "
                            "adhere to the family supplied or the family of the product"
                            " default supplied."
                        )
        return self


class ProductsSpec(FrozenModel):
    """Format for the Product 'spec' field.

    Uses FrozenModel, meaning no additional fields can be added.
    """

    products: List[Product] = Field(
        ...,
        description=(
            "A list of one or more products that fall under the same source name."
            "For example, Visible and Infrared under the 'abi' source name."
        ),
    )


class ProductPluginModel(PluginModel):
    """Product plugin format using pydantic."""

    model_config = ConfigDict(extra="allow")
    spec: ProductsSpec = Field(
        ..., description="A field representing a list of products."
    )
