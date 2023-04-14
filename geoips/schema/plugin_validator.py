"""Implements valdation machinery for YAML-based plugins."""

import yaml
from glob import glob
from importlib.resources import files
from pathlib import Path
import jsonschema

package_path = Path(files("geoips"))


def extend_with_default(validator_class):
    """Extend a jsonschema validator to make it respect default values.

    This will cause the validator to fill in fields that have default values. In
    cases where fields with default values are contained inside a mapping, that
    mapping must have `default: {}` and may not have `requires`.
    """
    validate_properties = validator_class.VALIDATORS["properties"]

    # @classmethod
    # def check_schema(cls, schema, format_checker=_UNSET):
    #     Validator = validator_for(cls.META_SCHEMA, default=cls)
    #     if format_checker is _UNSET:
    #         format_checker = Validator.FORMAT_CHECKER
    #     validator = Validator(
    #         schema=cls.META_SCHEMA,
    #         format_checker=format_checker,
    #     )
    #     for error in validator.iter_errors(schema):
    #         raise exceptions.SchemaError.create_from(error)

    def required_no_defaults(validator, required, instance, schema):
        print("IN REQUIRED")
        print("Schema", schema)
        print("Instance", instance)
        if not validator.is_type(instance, "object"):
            return

        properties = schema["properties"]

        for property in required:
            properties = schema["properties"]
            if property in properties and "default" in properties[property]:
                yield jsonschema.exceptions.ValidationError(
                    f"property {property!r} is both required and sets a default value"
                )
            if property not in instance:
                yield jsonschema.exceptions.ValidationError(
                    f"{property!r} is a required property"
                )
            # if property not in instance:
            #     if property not in properties or "default" not in properties[property]:
            #         yield jsonschema.exceptions.ValidationError(
            #             f"required property {property!r} "
            #             f"was not provided and has no default value."
            #         )

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
        {
            "required": required_no_defaults,
            "properties": set_defaults,
        },
    )


# Create a validator that respects defaults
DefaultValidatingValidator = extend_with_default(jsonschema.Draft202012Validator)


def get_all_schema():
    """Collect all of the interface schema"""
    schema_path = files("geoips.schema")

    schema_files = Path(f"{str(schema_path)}/").rglob("*.yaml")

    all_schema = {}
    for schema_file in schema_files:
        schema = yaml.safe_load(open(schema_file, "r"))

        print(f"Adding schema file {schema_file}")

        schema_id = schema["$id"]
        schema = yaml.safe_load(open(schema_file, "r"))
        print(f"Adding validator {schema_id}")

        try:
            DefaultValidatingValidator.check_schema(schema)
        except jsonschema.exceptions.SchemaError as err:
            raise jsonschema.exceptions.SchemaError(
                f"Invalid schema {schema_file}"
            ) from err
        all_schema[schema_id] = schema

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

    # Read the plugin
    plugin_yaml = yaml.safe_load(open(plugin_file, "r"))

    # Validate against the base schema
    # This ensures that "interface" and "family" are set correctly before trying to use
    # them
    validators["base"].validate(plugin_yaml)

    # Build the name of the schema to validate against
    interface = plugin_yaml["interface"]
    family = plugin_yaml["family"]
    print(f"Checking validator {interface}.{family}")
    validator_name = f"{interface}.{family}"
    if validator_name not in validators:
        raise jsonschema.exceptions.ValidationError(
            f"No validator found for the '{family}' family "
            f"in the '{interface}' interface."
        )
    print(f"Using validator {validator_name}")
    validator = validators[validator_name]
    validator.validate(plugin_yaml)

    return plugin_yaml
