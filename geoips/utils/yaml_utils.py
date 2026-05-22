# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Drop-in replacement for `import yaml` with duplicate key detection.

Usage:
    import geoips.utils.yaml_utils as yaml

`safe_load` and `safe_load_all` raise `DuplicateKeyError` on repeated keys.
All other yaml symbols (dump, SafeLoader, SafeDumper, ...) pass through unchanged.
"""

import logging
import yaml
import os
import re
from yaml import *  # noqa: F401, F403  -- intentional re-export

from geoips.errors import DuplicateKeyError, MissingEnvironmentVariableError

LOG = logging.getLogger(__name__)

ENV_VAR_PATTERN = re.compile(r".*?\$\{([^}{:]+)(:[^}]+)?\}.*?")
DEFAULT_SEP = ":"

# ---------------
# Constructors
# ---------------


def _construct_mapping_no_duplicates(loader, node):
    """Construct a YAML mapping while checking for duplicate keys.

    Parameters
    ----------
    loader : yaml.Loader
        The YAML loader instance processing the current document.
    node : yaml.MappingNode
        The mapping node being constructed.

    Returns
    -------
    dict
        The constructed mapping.

    Raises
    ------
    DuplicateKeyError
        If a duplicate key is found in the mapping.
    """
    # flatten "<<: *anchor" merge keys before checking
    #   a key that appears both explicitly and via merge will falsely raise
    loader.flatten_mapping(node)

    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if key in mapping:
            raise DuplicateKeyError(
                f"Duplicate key '{key}' found at "
                f"line {key_node.start_mark.line + 1}, "
                f"column {key_node.start_mark.column + 1}"
            )
        mapping[key] = loader.construct_object(value_node)
    return mapping


def _construct_env_var(loader, node):
    """Resolve a YAML !ENV node by substituting environment variables.

    Adapted from pyaml_env.parse_config.constructor_env_variables.
    Supports `${VAR}` and `${VAR:default}` forms, with multiple variables
    in a single scalar (e.g. `http://${HOST}:${PORT}`).

    Parameters
    ----------
    loader : yaml.Loader
        The YAML loader instance processing the current document.
    node : yaml.ScalarNode
        The scalar node tagged with `!ENV`.

    Returns
    -------
    str
        The scalar value with every `${VAR}` and `${VAR:default}` resolved.

    Raises
    ------
    MissingEnvironmentVariableError
        If a referenced variable is not set and no default was provided.
    """
    value = loader.construct_scalar(node)
    matches = ENV_VAR_PATTERN.findall(value)
    if not matches:
        return value

    full_value = value
    for group in matches:
        # `group` is a 2-tuple: (var_name, ':default' or '')
        env_var_name = group[0]
        env_var_name_with_default = "".join(group)

        default = None
        for segment in group:
            if DEFAULT_SEP in segment:
                _, default = segment.split(DEFAULT_SEP, 1)
                break

        env_value = os.environ.get(env_var_name)
        if env_value is not None:
            substituted = env_value
        elif default is not None:
            substituted = default
        else:
            raise MissingEnvironmentVariableError(
                f"Environment variable '{env_var_name}' is not set "
                f"and no default value was provided in the YAML !ENV tag"
            )

        full_value = full_value.replace(
            f"${{{env_var_name_with_default}}}",
            substituted,
        )
    return full_value


# ---------------
# YAML Loaders
# ---------------


class SafeLoaderNoDuplicates(yaml.SafeLoader):
    """A YAML SafeLoader that raises an error on duplicate mapping keys.

    Inherits all behaviour from `yaml.SafeLoader` but overrides the default
    mapping constructor to track keys that have already been seen within each
    mapping node.
    """

    pass


class EnvVarLoader(SafeLoaderNoDuplicates):
    """SafeLoader variant that resolves `!ENV` tags into environment variable values.

    Inherits duplicate-key detection from `SafeLoaderNoDuplicates`, so loading
    via `EnvVarLoader` enforces both duplicate detection and `!ENV` resolution.
    """

    pass


SafeLoaderNoDuplicates.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping_no_duplicates,
)


EnvVarLoader.add_constructor("!ENV", _construct_env_var)


# -------------------
# Callable Functions
# -------------------


def safe_load(stream, Loader=SafeLoaderNoDuplicates):
    """Load a single YAML document, raising on duplicate keys by default.

    Drop-in replacement for `yaml.safe_load` that uses
    `SafeLoaderNoDuplicates` to reject mappings with repeated keys.

    Parameters
    ----------
    stream : str or file-like
        YAML content to parse.
    Loader : yaml.SafeLoader subclass, optional
        Loader class to use. Defaults to `SafeLoaderNoDuplicates`, which raises
        `DuplicateKeyError` on repeated keys. Pass `yaml.SafeLoader` to restore
        standard behaviour without duplicate detection.

    Returns
    -------
    dict
        The parsed YAML document.

    Raises
    ------
    DuplicateKeyError
        If a duplicate key is detected and the default `Loader` is used.
    """
    return yaml.load(stream, Loader=Loader)  # nosec B506


def safe_load_all(stream, Loader=SafeLoaderNoDuplicates):
    """Load all YAML documents from a stream, raising on duplicate keys by default.

    Drop-in replacement for `yaml.safe_load_all` that uses
    `SafeLoaderNoDuplicates` to reject mappings with repeated keys.

    Parameters
    ----------
    stream : str or file-like
        YAML content to parse.
    Loader : yaml.SafeLoader subclass, optional
        Loader class to use. Defaults to `SafeLoaderNoDuplicates`, which raises
        `DuplicateKeyError` on repeated keys. Pass `yaml.SafeLoader` to restore
        standard behaviour without duplicate detection.

    Yields
    ------
    dict
        Each parsed YAML document.

    Raises
    ------
    DuplicateKeyError
        If a duplicate key is detected and the default `Loader` is used.
    """
    return yaml.load_all(stream, Loader=Loader)  # nosec B506


def parse_config(path):
    """Load a YAML file and resolve any `!ENV` tags.

    Drop-in replacement for `pyaml_env.parse_config(path)` adapted for
    GeoIPS. Uses `EnvVarLoader`, which also inherits duplicate-key
    detection from `SafeLoaderNoDuplicates`.

    Parameters
    ----------
    path : str
        Path to a YAML file. File-like objects are not supported in this
        release.

    Returns
    -------
    dict
        The parsed YAML document with `!ENV` tags resolved.

    Raises
    ------
    MissingEnvironmentVariableError
        If a `!ENV` tag references an unset variable with no default.
    DuplicateKeyError
        If any mapping contains duplicate keys.
    """
    with open(path, encoding="utf-8") as conf_data:
        return yaml.load(conf_data, Loader=EnvVarLoader)  # nosec B506
