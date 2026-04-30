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
from yaml import *  # noqa: F401, F403  -- intentional re-export

from geoips.errors import DuplicateKeyError

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


SafeLoaderNoDuplicates.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping_no_duplicates,
)


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
