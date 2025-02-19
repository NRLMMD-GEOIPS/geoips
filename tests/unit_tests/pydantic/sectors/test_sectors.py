"""Testing module for Pydantic SectorPluginModel."""

from pydantic_core._pydantic_core import ValidationError
import pytest
import yaml

from geoips.interfaces import sectors
from geoips.pydantic import sectors as sectors_schema


attr_model_map = {
    "projection": [sectors_schema.SectorProjection],
    "area_extent": [sectors_schema.SectorAreaExtent],
    "shape": [sectors_schema.SectorShape],
    "resolution": [sectors_schema.SectorResolution],
    "spec": [
        sectors_schema.AreaDefinitionSpec,
        sectors_schema.CenterSpec,
    ],
    "metadata": [
        sectors_schema.StaticMetadata,
        sectors_schema.BoxMetadata,
        sectors_schema.StitchedMetadata,
        sectors_schema.TCMetadata,
        sectors_schema.VolcanoMetadata,
    ],
    "plugin": [sectors_schema.SectorPluginModel],
}


def generate_id_bad_plugin(plugin):
    """Generate an ID from plg_pkg for the corresponding test.

    Parameters
    ----------
    plugin: dict
        - The poorly formatted plugin to validate.
    """
    return plugin["name"]


def generate_id(plg_pkg):
    """Generate an ID from plg_pkg for the corresponding test.

    Parameters
    ----------
    plg_pkg: tuple(str)
        - The name of the sector plugin and the package it came from.
    """
    return " ".join([plg_pkg[1], plg_pkg[0]])


def generate_static_sectors():
    """Generate a list of names and packages for all static sector plugins.

    Yields
    ------
    plg_pkg: tuple(str)
        - The name of the sector plugin and the package it came from.
    """
    sector_entries = sectors.registered_yaml_based_plugins["sectors"]
    for plugin_name in sector_entries:
        if sector_entries[plugin_name]["family"] == "area_definition_static":
            yield (plugin_name, sector_entries[plugin_name]["package"])


def get_validator(key):
    """Retrieve the appropriate pydantic model used to validate a plugin's attr.

    Returns
    -------
    validator: Class
        - The class used to validate a certain object.
    """
    if key == "region":
        return attr_model_map["metadata"]
    return attr_model_map[key]


def load_sector_attr(plugin_name, key, subkey=None, package="geoips"):
    """Load the afforementioned attribute from the specified sector plugin.

    Where plugin_name refers to the sector plugin and key refers to the top level
    attribute of that plugin.

    Parameters
    ----------
    plugin_name: str
        - The name of the sector plugin.
    key: str
        - The name of the top level attribute of that sector plugin.
    subkey: str, default=None
        - The name of subkey of the key attribute, if necessary.
    package: str, default="geoips"
        - The name of the package in which this sector plugin resides in.

    Returns
    -------
    attr: Any
        - The specified attribute.
    """
    try:
        plugin = sectors.get_plugin(plugin_name)
    except KeyError:
        # Try recreating the registry if the plugin cannot be found
        sectors.call_create_plugin_registries()
        plugin = sectors.get_plugin(plugin_name)

    if key == "plugin":
        attr = plugin
    elif subkey:
        attr = plugin[key].get(subkey, {})
    else:
        attr = plugin[key]

    return attr


def validate_sector_attr(plugin_name, key, subkey=None, package="geoips", attr=None):
    """Validate the corresponding attribute of a sector plugin.

    Where plugin_name refers to the sector plugin and key refers to the top level
    attribute of that plugin.

    Parameters
    ----------
    plugin_name: str
        - The name of the sector plugin.
    key: str
        - The name of the top level attribute of that sector plugin.
    subkey: str, default=None
        - The name of subkey of the key attribute, if necessary.
    package: str, default="geoips"
        - The name of the package in which this sector plugin resides in.
    attr: Any, default=None
        - The attribute to validate. If not provided, it will be retrieved from the
          corresponded plugin via sectors.get_plugin(plugin_name)[key][subkey]
          (if subkey provided)

    Returns
    -------
    valid: bool
        - Whether or not the corresponding attribute of the sector plugin was valid.

    Raises
    ------
    ValidationError:
        - A pydantic error specifying that the object returned is invalid for some
          reason.
    """
    if attr is None:
        attr = load_sector_attr(plugin_name, key, subkey, package)

    validator_key = subkey if subkey else key
    validators = get_validator(validator_key)

    for idx, validator in enumerate(validators):
        try:
            if isinstance(attr, dict):
                valid = validator(**attr)
            elif isinstance(attr, list) or isinstance(attr, tuple):
                valid = validator(*attr)
            else:
                valid = validator(attr)
        except (TypeError, ValidationError) as e:
            if len(validators) == 1:
                raise e
            elif idx == len(validators) - 1:
                raise e
            else:
                continue
        return valid


def validate_sector_attrs(plugin, attr=None, package=None):
    """Validate all of the attributes of the provided static sector plugin.

    Parameters
    ----------
    plugin: GeoIPS Sector Plugin or dict
        - The plugin to validate
    attr: Any, default=None
        - The attribute to validate. If not provided, it will be retrieved from the
          corresponded plugin via sectors.get_plugin(plugin_name)[key][subkey]
          (if subkey provided)
    package: str, default="geoips"
        - The package in which the static sector plugin comes from. If not provided and
          'attr' is None as well, assume we are loading from some YAML file which is not
          a registered plugin.
    """
    for key in ["metadata", "spec", "plugin"]:
        print(key)
        if key != "plugin" and isinstance(plugin[key], dict):
            for subkey in plugin[key]:
                if isinstance(plugin[key][subkey], dict):
                    print(subkey)
                    validate_sector_attr(
                        plugin["name"], key, subkey=subkey, package=package, attr=attr
                    )
        else:
            validate_sector_attr(plugin["name"], key, package=package, attr=attr)


@pytest.mark.parametrize("plg_pkg", generate_static_sectors(), ids=generate_id)
def test_sector_plugins(plg_pkg):
    """Perform validation on static sector plugins, including failing cases.

    Parameters
    ----------
    plg_pkg: tuple(str)
        - A tuple containing the name of the static sector plugin and the package it
          comes from.
    """
    plugin_name = plg_pkg[0]
    package = plg_pkg[1]
    plugin = load_sector_attr(plugin_name, "plugin", package=package)
    validate_sector_attrs(plugin, package=package)


@pytest.mark.parametrize(
    "plugin",
    yaml.safe_load_all(open("./test_cases/bad.yaml", mode="r")),
    ids=generate_id_bad_plugin,
)
def test_invalid_sector_plugins(plugin):
    """Ensure that the plugins provided are found to be invalid."""
    for test_case in [
        "metadata",
        "spec",
        "projection",
        "resolution",
        "shape",
        "area_extent",
    ]:
        try:
            if test_case in [
                "projection",
                "resolution",
                "shape",
                "area_extent",
            ]:
                attr = plugin["spec"][test_case]
            else:
                attr = plugin[test_case]
        except KeyError:
            continue
        validate_sector_attr(plugin["name"], test_case, test_case, attr=attr)
        pytest.xfail(plugin["name"])
