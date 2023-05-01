"""Implements validation machinery for YAML-based plugins."""

import yaml

from importlib.resources import files
from pathlib import Path
import jsonschema
from jsonschema.exceptions import ValidationError, SchemaError
import referencing
from referencing import jsonschema as refjs


JSONSCHEMA_DRAFT = "202012"
SCHEMA_PATH = files("geoips") / "schema"


def extend_with_default(validator_class):
    """Extend a jsonschema validator to make it respect default values.

    Note: This does not pollute the input validator object. Calling
    `jsonschema.validators.extend` returns a new object.

    This will cause the validator to fill in fields that have default values. In
    cases where fields with default values are contained inside a mapping, that
    mapping must have `default: {}` and may not have `requires`.
    """
    validate_properties = validator_class.VALIDATORS["properties"]

    def required_no_defaults(validator, required, instance, schema):
        print(f"IN REQUIRED: {instance}")
        if not validator.is_type(instance, "object"):
            return

        properties = schema["properties"]

        for property in required:
            properties = schema["properties"]
            if property in properties and "default" in properties[property]:
                yield ValidationError(
                    f"property {property!r} is both required and sets a default value"
                )
            if property not in instance:
                print(f"MISSING {property}")
                yield ValidationError(f"{property!r} is a required property")

    def set_defaults(validator, properties, instance, schema):
        """Apply default values when a missing property has a default value."""
        for property, subschema in properties.items():
            if "default" in subschema:
                instance.setdefault(property, subschema["default"])

        for error in validate_properties(
            validator,
            properties,
            instance,
            schema,
        ):
            yield error

    return jsonschema.validators.extend(
        validator_class,
        {
            "required": required_no_defaults,
            "properties": set_defaults,
        },
    )


def get_schemas(path, validator):
    """Collect all of the interface schema."""
    print(path)
    schema_files = Path(path).rglob("*.yaml")

    schemas = {}
    for schema_file in schema_files:
        print(f"Adding schema file {schema_file}")

        schema = yaml.safe_load(open(schema_file, "r"))
        schema_id = schema["$id"]

        try:
            validator.check_schema(schema)
        except SchemaError as err:
            raise SchemaError(f"Invalid schema {schema_file}") from err
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


class PluginValidator:
    """PluginValidator class."""

    _schema_path = SCHEMA_PATH
    _validator = getattr(jsonschema, f"Draft{JSONSCHEMA_DRAFT}Validator")

    schemas = get_schemas(_schema_path, _validator)
    validators = get_validators(schemas, _validator)

    def validate(self, plugin, validator_id=None):
        """Validate method."""
        # Pop off unit-test properties
        try:
            plugin.pop("error")
        except (KeyError, AttributeError, TypeError):
            pass
        try:
            plugin.pop("error_pattern", None)
        except (KeyError, AttributeError, TypeError):
            pass

        if not validator_id:
            self.validators["bases.top"].validate(plugin)
            validator_id = f"{plugin['interface']}.{plugin['family']}"
        try:
            validator = self.validators[validator_id]
        except KeyError:
            raise ValidationError(f"No validator found for {validator_id}")
        validator.validate(plugin)

        if "interface" in plugin and plugin["interface"] == "products":
            self.validate_products(plugin)
        if validator_id == "products.bases.product":
            self.validate_product(plugin)

        return plugin

    def validate_products(self, plugin):
        """Validate all products."""
        if plugin["family"] == "single":
            print("Validating single products")
            products = [plugin["spec"]["product"]]
        elif plugin["family"] == "list":
            print("Validating list products")
            products = plugin["spec"]["products"]
        for product in products:
            self.validate_product(product)

    def validate_product(self, product):
        """Validate single product."""
        print("In validate product")
        if "family" in product:
            print("Validating family-based product")
            family = product["family"]
            try:
                spec_validator = self.validators[f"product_defaults.specs.{family}"]
            except KeyError:
                raise ValidationError(
                    f"No product_defaults spec for family {family}", instance=product
                )
            spec_validator.validate(product["spec"])
        elif "product_defaults" in product:
            print("Validating product_defaults-based product")
            product_defaults = product["product_defaults"]
        else:
            raise ValidationError(
                f"Product {product['name']} did not specify either "
                f"'family' or 'product_defaults'."
            )
