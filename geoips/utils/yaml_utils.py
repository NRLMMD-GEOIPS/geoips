# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Module for safely loading YAML files with duplicate key detection.

Standard `yaml.safe_load` silently overwrites earlier values when a YAML mapping
contains duplicate keys. This module provides drop-in replacements that raise a
`DuplicateYamlKeyError` instead, so that plugin authors receive immediate feedback
when a workflow or other plugin YAML file accidentally reuses a key.
"""

import logging

import yaml

from geoips.errors import DuplicateYamlKeyError

LOG = logging.getLogger(__name__)


class SafeLoaderNoDuplicates(yaml.SafeLoader):
    """A YAML SafeLoader that raises an error on duplicate mapping keys.

    Inherits all behaviour from `yaml.SafeLoader` but overrides the default
    mapping constructor to track keys that have already been seen within each
    mapping node.
    """

    pass


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
    DuplicateYamlKeyError
        If a duplicate key is found in the mapping.
    """
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if key in mapping:
            raise DuplicateYamlKeyError(
                f"Duplicate key '{key}' found at "
                f"line {key_node.start_mark.line + 1}, "
                f"column {key_node.start_mark.column + 1}"
            )
        mapping[key] = loader.construct_object(value_node)
    return mapping


SafeLoaderNoDuplicates.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping_no_duplicates,
)


def yaml_safe_load(stream):
    """Load a single YAML document, raising on duplicate keys.

    Drop-in replacement for `yaml.safe_load` that uses
    `SafeLoaderNoDuplicates` to reject mappings with repeated keys.

    Parameters
    ----------
    stream : str or file-like
        The YAML content to parse.

    Returns
    -------
    dict
        The parsed YAML document.

    Raises
    ------
    DuplicateYamlKeyError
        If a duplicate key is detected in any mapping within the document.
    """
    return yaml.load(stream, Loader=SafeLoaderNoDuplicates)


def yaml_safe_load_all(stream):
    """Load all YAML documents from a stream, raising on duplicate keys.

    Drop-in replacement for `yaml.safe_load_all` that uses
    `SafeLoaderNoDuplicates` to reject mappings with repeated keys.

    Parameters
    ----------
    stream : str or file-like
        The YAML content to parse.

    Yields
    ------
    dict
        Each parsed YAML document.

    Raises
    ------
    DuplicateYamlKeyError
        If a duplicate key is detected in any mapping within any document.
    """
    return yaml.load_all(stream, Loader=SafeLoaderNoDuplicates)