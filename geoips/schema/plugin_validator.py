"""Implements valdation machinery for YAML-based plugins."""

import os
import yaml
from glob import glob
from importlib.resources import files
import jsonschema
# import geoips.schema.refResolver as rr

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

schema_path = files("geoips.schema")
# var = jsonschema.Draft202012Validator(rr.base_schema,resolver=rr.all_refs)
# print(var)
DefaultValidatingValidator = extend_with_default(jsonschema.Draft202012Validator)
# Don't use `schema_path.glob` since if it is a MultiplexedPath it won't have `glob`
schema_files = glob(str(schema_path / "*.yaml"))
all_schema = {}
validators = {}
for schema_file in schema_files:
    schema_name = os.path.splitext(os.path.basename(schema_file))[0]
    # print(schema_name)
    schema = yaml.safe_load(open(schema_file, "r"))

    DefaultValidatingValidator.check_schema(schema)
    all_schema[schema_name] = schema
    validators[schema_name] = DefaultValidatingValidator(schema)

def createInterfaceValidators(reference_dict):
    all_validators = {}
    for key in reference_dict:
        # uri = key
        schema_resolver = jsonschema.RefResolver.from_schema(reference_dict[key], store=reference_dict)
        all_validators[key] = DefaultValidatingValidator(reference_dict[key],resolver=schema_resolver)
    return all_validators

def validate(plugin_file):
    all_validators = createInterfaceValidators(all_schema)
    plugin_name = plugin_file.split("/")[-2]
    # print(plugin_name)
    """Validate the a YAML-based plugin."""
    plugin_yaml = yaml.safe_load(open(plugin_file, "r"))
    validator = all_validators[plugin_name]
    # print(type(validator))
    validator.validate(plugin_yaml)

    return plugin_yaml
