# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Products interface module."""

import logging

from jsonschema.exceptions import ValidationError

from geoips.geoips_utils import merge_nested_dicts
from geoips.interfaces.base import YamlPluginValidator, BaseYamlInterface
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


class ProductsInterface(BaseYamlInterface):
    """GeoIPS interface for Products plugins."""

    name = "products"
    use_pydantic = False

    def _create_registered_plugin_names(self, yaml_plugin):
        """Create a plugin name for plugin registry.

        This name is a tuple containing source_name and name.
        Overrides the same method from YamlPluginValidator.
        """
        names = []
        for source_name in yaml_plugin["source_names"]:
            names += [(source_name, yaml_plugin["name"])]
        return names

    def get_plugin_metadata(self, source_name, name):
        """Retrieve a product plugin's metadata.

        Where the metadata of the plugin matches the plugin's corresponding entry in the
        plugin registry.

        Parameters
        ----------
        source_name: str
            - The source (sensor) which this product is derived from.
        name: str
            - The name of the product plugin whose metadata we'd like to retrieve.

        Returns
        -------
        metadata: dict
            - A dictionary of metadata for the requested plugin.
        """
        return super().get_plugin_metadata((source_name, name))

    def get_plugin(
        self, source_name, name, product_spec_override=None, rebuild_registries=None
    ):
        """Retrieve a Product plugin by source_name, name, and product_spec_override.

        If product_spec_override dict is passed, values contained within
        product_spec_override will be used in place of those found in products
        list and product_defaults.

        product_spec_override[product_name] matches the format of the product
        "spec" field.

        Additionally, if the special key product_spec_override["all"] is included,
        it will apply to all products not specified by name within the dictionary.

        Parameters
        ----------
        source_name : str
            - The name the source which the product is derived from.
        name : str
            - The name the desired plugin.
        dict : str
            - Dictionary specifying what information of the product's spec that is to be
              overridden at runtime.
        rebuild_registries: bool (default=None)
            - Whether or not to rebuild the registries if get_plugin fails. If set to
              None, default to what we have set in geoips.filenames.base_paths, which
              defaults to True. If specified, use the input value of rebuild_registries,
              which should be a boolean value. If rebuild registries is true and
              get_plugin fails, rebuild the plugin registry, call then call
              get_plugin once more with rebuild_registries toggled off, so it only gets
              rebuilt once.
        """
        prod_plugin = super().get_plugin((source_name, name), rebuild_registries)
        if product_spec_override is not None:
            # Default to no override arguments
            override_args = {}
            # If available, use the current product's override values
            if name in product_spec_override:
                override_args = product_spec_override[name]
            # Otherwise, if "all" specified, use those override values
            elif "all" in product_spec_override:
                override_args = product_spec_override["all"]
            replace_arg = False
            # NOTE: this is a top-level field, where if you set
            # product_spec_override:
            #   spec:
            #     replace: true
            # It will automatically replace ALL fields found in
            # the original product spec and also found in the
            # override with what is specified in the override
            # in its entirety, without merging.  This is not
            # terribly useful overall - we probably want this
            # sort of capability in the end, but more flexible
            # and able to be applied to only specific fields,
            # etc.  This is a brute force method to at least
            # allow overriding entire fields.
            if product_spec_override.get("replace"):
                replace_arg = True
            prod_plugin["spec"] = merge_nested_dicts(
                prod_plugin["spec"], override_args, in_place=False, replace=replace_arg
            )

        return prod_plugin

    def get_plugins(self):
        """Retrieve a plugin by name."""
        plugins = []
        for source_name in self.plugin_registry.registered_plugins["yaml_based"][
            self.name
        ].keys():
            for subplg_name in self.plugin_registry.registered_plugins["yaml_based"][
                self.name
            ][source_name].keys():
                plugins.append(self.get_plugin(source_name, subplg_name))
        return plugins

    def plugin_is_valid(self, source_name, name):
        """Test that the named plugin is valid."""
        try:
            self.get_plugin(source_name, name)
            return True
        except ValidationError:
            return False

    def test_interface(self):
        """Test interface method."""
        plugins = self.get_plugins()
        all_valid = self.plugins_all_valid()
        family_list = []
        plugin_ids = {}
        for plugin in plugins:
            if plugin.family not in family_list:
                family_list.append(plugin.family)
                plugin_ids[plugin.family] = []
            plugin_ids[plugin.family].append(plugin.id)

        output = {
            "all_valid": all_valid,
            "by_family": plugin_ids,
            "validity_check": {},
            "family": {},
            "func": {},
            "docstring": {},
        }
        for curr_family in plugin_ids:
            for curr_id in plugin_ids[curr_family]:
                output["validity_check"][curr_id] = self.plugin_is_valid(*curr_id)
                output["func"][curr_id] = self.get_plugin(*curr_id)
                output["family"][curr_id] = curr_family
                output["docstring"][curr_id] = output["func"][curr_id].docstring
        return output


products = ProductsInterface()
