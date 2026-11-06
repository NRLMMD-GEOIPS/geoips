# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Products base plugin module."""

import logging

from jsonschema.exceptions import ValidationError

from geoips.geoips_utils import merge_nested_dicts
from geoips.interfaces.base import YamlPluginValidator
from geoips.interfaces.yaml_based.product_defaults import product_defaults

LOG = logging.getLogger(__name__)


class ProductsPluginValidator(YamlPluginValidator):
    """Validator for Products plugins.

    This differs from other validators for two reasons:

    1. Most plugins are identified solely by 'name'. Products are identified by
       'source_name' and 'name.
    2. Most plugins supply their 'family' directly. Products can supply it directly, but
       can, alternatively, specify a 'product_defaults' plugin from which to pull
       'family' and most other properties. This validator handles filling in a product
       plugin based on its specified product defaults plugin.
    """

    def validate(self, plugin, validator_id=None):
        """Validate a Products plugin against the relevant schema.

        The relevant schema is determined based on the interface and family of the
        plugin.
        """
        if "product_defaults" in plugin:
            if "family" in plugin:
                raise ValidationError(
                    "Properties 'family' and 'product_defaults' are mutually exclusive."
                )
            self.validate_product(plugin)
        else:
            try:
                plugin = super().validate(plugin, validator_id=validator_id)
            except ValidationError as resp:
                raise ValidationError(
                    f"{resp}: Trouble validating plugin '{plugin.get('name')}'\n"
                    f"in interface '{plugin.get('interface')}'\n"
                    f"located at '{plugin.get('abspath')}'\n"
                    f"from package '{plugin.get('package')}' "
                ) from resp

        return plugin

    def validate_product(self, product):
        """Validate single product."""
        LOG.debug("In validate product")
        if "family" in product:
            LOG.debug("Validating family-based product")
            family = product["family"]
            try:
                spec_validator = self.validators[f"product_defaults.specs.{family}"]
            except KeyError:
                raise ValidationError(
                    f"No product_defaults spec for family '{family}'", instance=product
                )
            spec_validator.validate(product["spec"])
        elif "product_defaults" in product:
            defaults = product_defaults.get_plugin(product.pop("product_defaults"))
            product["family"] = defaults["family"]

            LOG.debug("Validating product_defaults-based product")
            # This updates missing values in spec from defaults but leaves existing
            # values alone. Using update here ensures that we're updating in-place
            # rather than creating a new dictionary.
            merge_nested_dicts(product, defaults)
        else:
            raise ValidationError(
                f"Product '{product['name']}' did not specify either "
                f"'family' or 'product_defaults'."
            )
        return product
