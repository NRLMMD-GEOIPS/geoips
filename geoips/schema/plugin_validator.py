"""Implements valdation machinery for YAML-based plugins."""

import os
import yaml
from glob import glob
from importlib.resources import files
import jsonschema


def extend_with_default(validator_class):
    validate_properties = validator_class.VALIDATORS["properties"]

    def set_defaults(validator, properties, instance, schema):
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


DefaultValidatingValidator = extend_with_default(jsonschema.Draft202012Validator)
schema_path = files("geoips.schema")
# Don't use `schema_path.glob` since if it is a MultiplexedPath it won't have `glob`
schema_files = glob(str(schema_path / "*.yaml"))
schema_files += glob(str(schema_path / "*/*.yaml"))
all_schema = {}
validators = {}
for schema_file in schema_files:
    schema_name = (
        schema_file.replace(str(schema_path) + "/", "")
        .replace("/", ".")
        .replace(".yaml", "")
    )
    schema = yaml.safe_load(open(schema_file, "r"))
    print(f"Adding validator {schema_name}")
    DefaultValidatingValidator.check_schema(schema)
    all_schema[schema_name] = schema
    validators[schema_name] = DefaultValidatingValidator(schema)


def validate(plugin_file):
    """Validate the a YAML-based plugin."""
    plugin_yaml = yaml.safe_load(open(plugin_file, "r"))
    validator = validators[plugin_yaml["interface"]]
    validator.validate(plugin_yaml)

    return plugin_yaml
