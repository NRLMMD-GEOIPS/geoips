"""Implements valdation machinery for YAML-based plugins."""

import os
import yaml
from glob import glob
from importlib.resources import files
import jsonschema


schema_path = files("geoips.schema")
# Don't use `schema_path.glob` since if it is a MultiplexedPath it won't have `glob`
schema_files = glob(str(schema_path / "*.yaml"))
all_schema = {}
validators = {}
for schema_file in schema_files:
    schema_name = os.path.splitext(os.path.basename(schema_file))[0]
    schema = yaml.safe_load(open(schema_file, "r"))
    jsonschema.Draft202012Validator.check_schema(schema)
    all_schema[schema_name] = schema
    jsonschema.Draft202012Validator.check_schema(schema)
    validators[schema_name] = jsonschema.Draft202012Validator(schema)


def validate(plugin_file):
    """Validate the a YAML-based plugin."""
    plugin_yaml = yaml.safe_load(open(plugin_file, "r"))
    validator = validators[plugin_yaml["interface"]]
    validator.validate(plugin_yaml)

    return plugin_yaml
