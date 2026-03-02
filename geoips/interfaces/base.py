# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Base classes for interfaces, plugins, and plugin validation machinery."""

# cspell:ignore refjs

import yaml
import logging

from importlib.resources import files
from pathlib import Path
import jsonschema
import referencing
from referencing import jsonschema as refjs
from jsonschema.exceptions import ValidationError, SchemaError

from geoips.errors import PluginError
from pluginify.interfaces.base import BaseYamlInterface

LOG = logging.getLogger(__name__)


JSONSCHEMA_DRAFT = "202012"
SCHEMA_PATH = files("geoips") / "schema"


def get_schemas(path, validator):
    """Collect all of the interface schema."""
    schema_files = Path(path).rglob("*.yaml")

    schemas = {}
    for schema_file in schema_files:
        LOG.debug(f"Adding schema file {schema_file}")

        with open(schema_file, "r") as fo:
            schema = yaml.safe_load(fo)
        schema_id = schema["$id"]

        try:
            validator.check_schema(schema)
        except SchemaError as err:
            raise SchemaError(f"Invalid schema '{schema_file}'") from err
        schemas[schema_id] = schema

    return schemas


def get_validators(schema_dict, validator_class):
    """Create validators for each schema in `schema_dict`.

    Parameters
    ----------
    schema_dict : dict
        A dictionary whose keys are schema `$id` and whose values are the full
        schema.

    Returns
    -------
    dict
        A dictionary whose keys are schema `$id` and whose values are `jsonschema`
        validator instances.
    """
    # This is the jsonschema draft implemention from the referencing package
    # It is used for creating the "resources" and "registry" that link together
    # the references.
    #
    # This could likely have a better variable name, but I don't really know what to
    # call it...
    ref = getattr(refjs, f"DRAFT{JSONSCHEMA_DRAFT}")
    resources = [(name, ref.create_resource(sch)) for name, sch in schema_dict.items()]
    registry = referencing.Registry().with_resources(resources)

    # Loop over the available schema and build a dictionary whose keys are the $ids
    # of the schema and whose values are their associated validators. These validators
    # can be used to validate yaml against their schema.
    validators = {}
    for name, schema in schema_dict.items():
        validators[name] = validator_class(schema, registry=registry)
    return validators


class YamlPluginValidator:
    """PluginValidator class."""

    _schema_path = SCHEMA_PATH
    _validator = getattr(jsonschema, f"Draft{JSONSCHEMA_DRAFT}Validator")

    @property
    def schemas(self):
        """Return a list of jsonschema schemas for GeoIPS.

        This performs a lazy-load for the schema to avoid loading them if not
        needed. This reduces the import time for geoips.interfaces.
        """
        if not hasattr(self, "_schemas"):
            self._schemas = get_schemas(self._schema_path, self._validator)
        return self._schemas

    @property
    def validators(self):
        """Return schema validators.

        This performs a lazy-load for the validators to avoid loading them if not
        needed. This reduces the import time for geoips.interfaces.
        """
        if not hasattr(self, "_validators"):
            self._validators = get_validators(self.schemas, self._validator)
        return self._validators

    def validate(self, plugin, validator_id=None):
        """Validate a YAML plugin against the relevant schema.

        The relevant schema is determined based on the interface and family of the
        plugin.
        """
        # Pop off unit-test properties
        try:
            plugin.pop("error")
        except (KeyError, AttributeError, TypeError):
            pass
        try:
            plugin.pop("error_pattern", None)
        except (KeyError, AttributeError, TypeError):
            pass

        # This is a temporary fix as we transition to using one top-level schema per
        # interface. As we transition, add more exceptions here.
        if not validator_id and plugin["interface"] == "sectors":
            if plugin["family"] == "generated":
                validator_id = "sectors.generated"
            else:
                validator_id = "sectors.static"

        if not validator_id:
            self.validators["bases.top"].validate(plugin)
            validator_id = f"{plugin['interface']}.{plugin['family']}"

        try:
            if validator_id == "workflows.order_based":
                return plugin
            validator = self.validators[validator_id]
        except KeyError as err:
            if validator_id == "workflows.order_based":
                return plugin
            raise ValidationError(
                f"No validator found for '{validator_id}'"
                f"\nfrom plugin '{plugin['name']}'"
                f"\nin interface '{plugin['interface']}'"
            ) from err

        # The error ourput by `validator.validate(plugin)` is being used for testing
        # in the unit tests. str(err) MUST be included in the raised exception string
        # to ensure unit tests continue to pass.
        #
        # See issue #303
        try:
            validator.validate(plugin)
        except ValidationError as err:
            try:
                plg_name = plugin.get("name")
                plg_pkg = plugin.get("package")
                plg_interface = plugin.get("interface")
                plg_abspath = plugin.get("abspath")
            except AttributeError:
                raise ValidationError(
                    f"{str(err)}: No 'get()' method found on plugin object."
                ) from err
            except KeyError:
                missing_keys = []
                for key in ["name", "package", "interface", "abspath"]:
                    if key not in plugin:
                        missing_keys.append(key)
                raise ValidationError(
                    f"{str(err)}: Plugin missing required keys: {missing_keys}."
                ) from err
            raise ValidationError(
                f"{str(err)}: "
                "\nFailed to validate plugin with json schema"
                f"\non plugin '{plg_name}'"
                f"\nfrom package '{plg_pkg}' "
                f"\nwithin interface '{plg_interface}' "
                f"\nat '{plg_abspath}'"
            ) from err

        if "family" in plugin and plugin["family"] == "list":
            plugin = self.validate_list(plugin)

        return plugin

    def validate_list(self, plugin):
        """Validate a list of YAML plugins.

        Some interfaces allow a 'list' family. These list plugins will contain a
        property that is the same as the interface's name. Under that is a list of
        individual plugins.

        This function will add the interface property to each plugin in the list, then
        validate each plugin.
        """
        valid_list_families = ["products"]
        if plugin["interface"] not in valid_list_families:
            raise NotImplementedError(
                "Unable to handle plugins of family 'list' for"
                f"'{plugin['interface']} interface."
                f"\nPlugins from family 'list' are currently only handled for "
                f"the following interfaces: '{valid_list_families}'."
            )
        # Lists should use their interface name to denote the beginning of the list
        for sub_plugin in plugin["spec"][plugin["interface"]]:
            sub_plugin["interface"] = plugin["interface"]
            try:
                self.validate(sub_plugin)
            except PluginError as resp:
                raise PluginError(
                    f"{resp}: Trouble validating sub_plugin '{sub_plugin.get('name')}' "
                    f"\non plugin '{plugin.get('name')}'"
                    f"\nfrom package '{plugin.get('package')}' "
                    f"\nat '{plugin.get('abspath')}'"
                ) from resp
        return plugin


def plugin_repr(obj):
    """Repr plugin string."""
    return f'{obj.__class__}(name="{obj.name}", module="{obj.module}")'


class BaseYamlInterface(BaseYamlInterface):
    """Base class for GeoIPS yaml-based plugin interfaces.

    This class should not be instantiated directly. Instead, interfaces should be
    accessed by importing them from ``geoips.interfaces``. For example:
    ```
    from geoips.interfaces import products
    ```
    will retrieve an instance of ``ProductsInterface`` which will provide access to
    the GeoIPS products plugins.
    """

    validator = YamlPluginValidator()
