"""Pydantic PluginModel for GeoIPS Product plugins.

Validates Product plugins using pydantic. Intended to be a 'carryover' model which will
be used until we fully switch over to using workflow plugins.
"""

from typing import List, Literal, Union

from pydantic import ConfigDict, Field, model_validator, RootModel
import yaml

from geoips.geoips_utils import merge_nested_dicts
from geoips.pydantic.bases import (
    FrozenModel,
    PermissiveFrozenModel,
    PythonIdentifier,
    PluginModel,
)

FAMILIES_CHECKED_AGAINST = [
    "algorithm_colormapper",
    "algorithm_interpolator_colormapper",
    "algorithm",
    "interpolator_algorithm_colormapper",
    "interpolator_algorithm",
    "interpolator",
]


class ModulePluginArgumentsModel(PermissiveFrozenModel):
    """Format specifying which module plugin to use and the arguments to provide to it.

    Normally one of 'algorithm', 'colormapper', 'interpolator', but can be other types
    of module plugins as well (such as 'coverage_checker').
    """

    name: PythonIdentifier = Field(
        ..., description="The name of the module plugin to be used."
    )
    arguments: dict = Field(
        ...,
        description=(
            "A dictionary of arbitrary arguments applicable to this specific plugin."
        ),
    )


class SpecPlugin(FrozenModel):
    """Model containing the name of the module plugin and the arguments to feed it."""

    plugin: ModulePluginArgumentsModel = Field(
        ...,
        desciption=(
            "The specification of the module plugin being overridden or implemented "
            "directly."
        ),
    )


class ProductDefaultSpec(PermissiveFrozenModel):
    """Format of the argument specifications for a product default plugin.

    Additional fields may be added as needed.

    As well, you can add as many arguments to a certain plugin as needed. Keep in mind
    these arguments must be present in the actual module plugin.
    """

    algorithm: SpecPlugin = Field(
        None, description="The specification of an algorithm plugin."
    )
    colormapper: SpecPlugin = Field(
        None, description="The specification of an colormapper plugin."
    )
    interpolator: SpecPlugin = Field(
        None, description="The specification of an interpolator plugin."
    )
    windbarb_plotter: SpecPlugin = Field(
        None, description="The specification of an windbarb_plotter plugin."
    )
    coverage_checker: SpecPlugin = Field(
        None, description="The specification of an coverage_checker plugin."
    )
    pad_area_definition: bool = Field(
        None, description="Whether or not to pad your area definition if specified."
    )
    mtif_type: str = Field(None, description="The format of METOC TIFF to output.")
    display_name: str = Field(None, description="The display name of your product.")


class ProductDefaultPluginModel(PluginModel):
    """Format for product_default plugins.

    Validated with pydantic models.
    """

    model_config = ConfigDict(extra="allow")
    spec: ProductDefaultSpec = Field(
        ..., description="The specification of a product default plugin."
    )

    @model_validator(mode="before")
    def _validate_plugins_if_exist(self):
        """Validate that if a plugin is provided, it is part of the family provided.

        Where family comes from spec.family or spec.product_defaults.family.
        """
        family_name = self["family"]

        if family_name in FAMILIES_CHECKED_AGAINST:
            # Only validating for the alg-cmap-int -based families currently
            for plugin_type in ["algorithm", "colormapper", "interpolator"]:
                if plugin_type in self["spec"]:
                    if (
                        plugin_type not in family_name
                        and self["spec"][plugin_type] is not None
                    ):
                        raise ValueError(
                            f"Error: '{plugin_type}' plugin supplied but that does not "
                            "adhere to the family supplied or the family of the product"
                            " default supplied."
                        )
                elif plugin_type in family_name and plugin_type not in self["spec"]:
                    raise ValueError(
                        "Error: Your product or product default is missing required "
                        f"'{plugin_type}' plugin based on the family provided."
                    )
        return self


class ProductSpec(ProductDefaultSpec):
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


class ProductsListSpec(FrozenModel):
    """Format for the Product 'spec' field.

    Uses FrozenModel, meaning no additional fields can be added.
    """

    # Quotes are used here as this is a forward reference. Haven't found a workaround to
    # this yet.
    products: List["SingleProductPluginModel"] = Field(
        ...,
        description=(
            "A list of one or more products that fall under the same source name."
            "For example, Visible and Infrared under the 'abi' source name."
        ),
    )


class ProductsListPluginModel(PluginModel):
    """Format for how to specify a list of product plugins."""

    spec: ProductsListSpec = Field(
        ..., description="The specification format of a plugin list."
    )


class SingleProductPluginModel(PluginModel):
    """Format for how to specify a singular product plugin."""

    model_config = ConfigDict(extra="allow")

    interface: Literal["products"] = Field("products", frozen=True)

    source_names: List[str] = Field(
        ...,
        description=(
            "A list of strings representing the source(s) this product is derived from."
            "Currently doesn't have to be a valid python identifier as we have some "
            "cases that don't adhere to that (such as amsu-a_mhs)."
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
    # Using quotes around the classes as we need forward references. No other way around
    # this that I've found so far.
    spec: ProductSpec = Field(
        ...,
        description=(
            "The specification of specific arguments for this product plugin. "
            "Additionally, can override arguments specified in the product_defaults "
            "plugin it referenced if applicable."
        ),
    )

    # This runs after 'check_family_pd_xor'
    @model_validator(mode="before")
    @classmethod
    def load_product_default(cls, self):
        """If a product_defaults entry has been provided, load it."""
        if self.get("product_defaults"):
            # Doing this here as this will cause a circular import if used at the top of
            # the file
            from geoips.interfaces import product_defaults

            abspath = product_defaults.get_plugin(self["product_defaults"])["abspath"]
            yam = yaml.safe_load(open(abspath, "r"))
            # This assigns the actual model to the product defaults attribute. We then
            # merge that (keeping original product contents) with the products spec.
            self["product_defaults"] = ProductDefaultPluginModel(**yam)
            cls._override_product_defaults(self)
            # At the end of this function, we remove the product defaults attribute
            # entirely and fill its family in the corresponding attribute instead.

        cls._validate_plugins_if_exist(self)

        return self

    # NOTE: model validators using mode before run from bottom to top.
    # This runs before 'load_product_default'
    @model_validator(mode="before")
    def check_family_pd_xor(self):
        """Validate that either family or product_defaults is provided xor fashion.

        Meaning, only one of those options can be provided, not both or none.
        """
        if (self.get("family") is None and self.get("product_defaults") is None) or (
            self.get("family") is not None and self.get("product_defaults") is not None
        ):
            raise ValueError(
                "You must provide exactly one of 'family' or 'product_defaults'."
            )
        return self

    # Not implementing as a model validator as it would not consistently run last.
    def _validate_plugins_if_exist(self):
        """Validate that if a plugin is provided, it is part of the family provided.

        Where family comes from spec.family or spec.product_defaults.family.
        """
        family_name = self["family"]

        if family_name in FAMILIES_CHECKED_AGAINST:
            # Only validating for the alg-cmap-int -based families currently
            for plugin_type in ["algorithm", "colormapper", "interpolator"]:
                if plugin_type in self["spec"]:
                    if (
                        plugin_type not in family_name
                        and self["spec"][plugin_type] is not None
                    ):
                        raise ValueError(
                            f"Error: '{plugin_type}' plugin supplied but that does not "
                            "adhere to the family supplied or the family of the product"
                            " default supplied."
                        )
                elif plugin_type in family_name and plugin_type not in self["spec"]:
                    raise ValueError(
                        "Error: Your product or product default is missing required "
                        f"'{plugin_type}' plugin based on the family provided."
                    )
        return self

    def _override_product_defaults(self):
        """Override the contents of product defaults if applicable."""
        if self["product_defaults"]:
            self["spec"] = merge_nested_dicts(
                self["spec"],
                self["product_defaults"].spec.dict(),
                in_place=False,
                replace=False,
            )
            self["family"] = self["product_defaults"].family
            self.pop("product_defaults")

        # Remove all top level null values from the product's spec. I.e:
        # interpolator=null (cannot remove easily via pydantic)
        self["spec"] = {k: v for k, v in self["spec"].items() if v is not None}

        return self


# Discriminated Union via RootModel
class _ProductPluginUnion(
    RootModel[Union[ProductsListPluginModel, SingleProductPluginModel]]
):
    """Private root model to unpack via ProductPluginModel."""

    root: Union[ProductsListPluginModel, SingleProductPluginModel]


class ProductPluginModel:
    """The format of a singular product plugin or a list of them."""

    def __new__(cls, **data):
        """Create a new instance of a ProductPluginModel exposing the subclass of root.

        Where root is the attribute used to access either type of model used to
        construct a ProductPluginModel.

        I.e. '_ProductPluginUnion(**data).root = Real Model' # NOQA RS210
        """
        parsed_model = _ProductPluginUnion(**data).root
        return parsed_model
