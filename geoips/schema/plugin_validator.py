"""Implements valdation machinery for YAML-based plugins."""

import os
import yaml
from glob import glob
from importlib.resources import files
import jsonschema
import numpy as np


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
    """Read all interface schema provided by GeoIPS.

    Returns
    -------
    dict
        A dictionary whose keys are the $id of each schema and whose values are
        the schema themselves.
    """
    schema_path = files("geoips.schema")
    # Don't use `schema_path.glob` since if it is a MultiplexedPath it won't have `glob`
    schema_files = glob(str(schema_path / "*.yaml"))
    schema_files += glob(str(schema_path / "*/*.yaml"))

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

        DefaultValidatingValidator.check_schema(schema)
        all_schema[schema_name] = schema

    return all_schema


def get_validators(schema_dict,display=False):
    """Create validators for each schema in the input dictionary of schema.

    Parameters
    ----------
    schema_dict : dict
        A dictionary whose keys are the $id of each schema and whose values are
        the schema themselves.

    Returns
    -------
    dict
        A dictionary whose keys are the name of each validator and whose values are
        jsonschema validators. The names are formatted as `interface.family`.
    """
    validators = {}
    for name, schema in schema_dict.items():
        resolver = jsonschema.RefResolver.from_schema(schema, store=schema_dict)
        if display:
            for key in list(resolver.store.keys()): #displays the resolved references for each schema provided.
                resolver.resolve(key)
        validators[name] = DefaultValidatingValidator(schema, resolver=resolver)
    return validators

all_schema = get_all_schema()
validators = get_validators(all_schema)
product_template_args_mapping = {"algorithm": "alg_args", "interpolation": "interp_args", "colormap": "cmap_args"}

def merge_product_with_product_template(plugin_yaml):
    """Update the provided product_inputs yaml plugin to include the additional values held in the correlated product_templates plugin.

    Parameters
    ----------
    yaml_plugin : dict
        A dictionary whose keys are the objects of each schema and whose values are
        the yaml_plugin data for the associated key.

    Returns
    -------
    dict
        A dictionary whose keys/values have been updated to include the additional values held in the correlated product_templates plugin.
    """
    correlated_product_template_plugins = {}
    product_template_files = glob("geoips/interface_modules/product_templates/**/*.yaml")
    other_product_temp_files = glob("geoips/interface_modules/product_templates/*.yaml")
    for f in other_product_temp_files:
        product_template_files.append(f)
    for product in range(len(plugin_yaml["spec"]["products"])):
        pname = plugin_yaml["spec"]["products"][product]["name"]
        file_idx = np.argmax([pname + ".yaml" in filepath for filepath in product_template_files])
        if file_idx >= 0:
            correlated_product_template_plugins[pname] = yaml.safe_load(open(product_template_files[file_idx],"r"))
            for product_template_key in correlated_product_template_plugins[pname]["spec"]:
                product_key = product_template_key
                if product_template_key in product_template_args_mapping:
                    product_key = product_template_args_mapping[product_template_key]
                product_keys = list(plugin_yaml["spec"]["products"][product].keys())
                if product_key not in product_keys:
                    plugin_yaml["spec"]["products"][product][product_key] = correlated_product_template_plugins[pname]["spec"][product_template_key]
    return plugin_yaml


def validate(plugin_file):
    """Validate the a YAML-based plugin.
    
    Parameters
    ----------
    plugin_file : string
        A string which represents the path of the yaml_plugin to be validated against.

    Returns
    -------
    dict
        A dictionary of the associated plugin_file if the corresponding yaml plugin validated without errors.
    """
    plugin_yaml = yaml.safe_load(open(plugin_file, "r"))
    validator_name = plugin_yaml["interface"]
    if "product_inputs" in validator_name: #dynamically add reference to product_templates
        plugin_yaml = merge_product_with_product_template(plugin_yaml)
    family = plugin_yaml["metadata"]["family"]
    if f"{validator_name}.{family}" in validators:
        validator_name = f"{validator_name}.{family}"
    print(f"Using validator {validator_name}")
    validator = validators[validator_name]
    validator.validate(plugin_yaml)

    return plugin_yaml
