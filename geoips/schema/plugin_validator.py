"""Implements valdation machinery for YAML-based plugins."""

import os
import yaml
from glob import glob
from importlib.resources import files
import jsonschema


def extend_with_default(validator_class):
    """Extend a jsonschema validator to make it respect default values.

    This will cause the validator to fill in fields that have default values. In
    cases where fields with default values are contained inside a mapping, that
    mapping must have `default: {}` and may not have `requires`.
    """
    validate_properties = validator_class.VALIDATORS["properties"]

    def set_defaults(validator, properties, instance, schema):
        print("In set_defaults")
        print(properties)
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
        {"properties": set_defaults},
    )


# Create a validator that respects defaults
DefaultValidatingValidator = extend_with_default(jsonschema.Draft202012Validator)


def get_all_schema():
    """Collect all of the interface schema"""
    schema_path = files("geoips.schema")
    # Don't use `schema_path.glob` since if it is a MultiplexedPath it won't have `glob`
    schema_files = glob(str(schema_path / "*.yaml"))
    schema_files.append(str(schema_path / "product_templates/algorithm_colormap.yaml"))
    schema_files.append(
        str(schema_path / "product_templates/algorithm_interpolation_colormap.yaml")
    )
    schema_files.append(
        str(schema_path / "product_templates/interpolation_algorithm_colormap.yaml")
    )
    # schema_files += glob(str(schema_path / "*.yaml"))

    all_schema = {}
    for schema_file in schema_files:
        schema = yaml.safe_load(open(schema_file, "r"))
        schema_name = (
            schema_file.replace(str(schema_path) + "/", "")
            .replace("/", ".")
            .replace(".yaml", "")
        )
        schema = yaml.safe_load(open(schema_file, "r"))
        print(f"Adding validator {schema_name}")

        try:
            DefaultValidatingValidator.check_schema(schema)
        except jsonschema.exceptions.SchemaError as err:
            raise ValueError(f"Invalid schema {schema_file}") from err
        all_schema[schema_name] = schema

    return all_schema


def get_validators(schema_dict):
    validators = {}
    for name, schema in schema_dict.items():
        resolver = jsonschema.RefResolver.from_schema(schema, store=schema_dict)
        validators[name] = DefaultValidatingValidator(schema, resolver=resolver)
    return validators


all_schema = get_all_schema()
validators = get_validators(all_schema)


def validate(plugin_file):
    """Validate the a YAML-based plugin."""
    plugin_yaml = yaml.safe_load(open(plugin_file, "r"))
    interface = plugin_yaml["interface"]
    family = plugin_yaml["family"]
    print(f"Checking validator {interface}.{family}")
    if f"{interface}.{family}" in validators:
        validator_name = f"{interface}.{family}"
    else:
        validator_name = interface
    print(f"Using validator {validator_name}")
    validator = validators[validator_name]
    validator.validate(plugin_yaml)

    return plugin_yaml
