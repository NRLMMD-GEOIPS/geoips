# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Test retrieving GeoIPS and other plugin packages' plugins."""

from importlib import reload
import pytest
from pydantic import ValidationError as PydanticValidationError

from geoips import interfaces
from geoips.errors import PluginError, PluginValidationError
from geoips import plugin_registry as plugin_registry_module
from geoips.pydantic_models.v1.sectors import SectorPluginModel


def yield_interface_plugin_tuples():
    """Yield tuples containing information for one call to `test_get_plugin`.

    Yield tuples (interface_name, plugin_name_tuple, expected_output) to use when
    attempting to load a plugin in the `test_get_plugin` function. The tuple will
    contain three elements:

    - interface_name:
        - The name of the interface that we want to attempt to load a plugin from.
    - plugin_name_tuple:
        - A tuple containing one or two strings defining which plugin should be
            loaded. Two strings is used for the Products interface and one string is
            used for all other interfaces.
    - expected_output:
        - A string describing the expected outcome. This is used in the
            `test_get_plugin` function to determine which part of the logic to follow
            and how to test the results.
    """
    registry = plugin_registry_module.plugin_registry.registered_plugins
    for plugin_type in registry:
        if plugin_type == "text_based":
            # Functionality is not yet set up for this. Once PR #504 gets merged, we can
            # remove this.
            continue
        for interface_name in registry[plugin_type]:
            if interface_name == "workflows":
                pass
            elif interface_name == "products":
                # Products have another level which is 'source_name', so we need
                # different functionality here to handle that
                for source_name in registry[plugin_type][interface_name]:
                    products = registry[plugin_type][interface_name][source_name]
                    for idx, prod_name in enumerate(products):
                        # Only add up to the first 5 plugins of the first source name
                        if idx > 4:
                            break
                        yield (interface_name, (source_name, prod_name), "normal")
                    break
            else:
                for idx, plugin_name in enumerate(
                    registry[plugin_type][interface_name]
                ):
                    # Only add up to the first 5 plugins of this interface
                    if idx > 4:
                        break
                    yield (interface_name, (plugin_name,), "normal")
    # Test that retrieving a fake plugin raises a PluginError
    yield ("algorithms", ("fake_algorithm_plugin",), "no_plugin")
    reload(plugin_registry_module)
    # Test that retrieving a fake plugin without rebuilding the registry raises a
    # PluginError
    yield ("algorithms", ("another_fake_algorithm_plugin",), "no_rebuild")
    registry = plugin_registry_module.plugin_registry.registered_plugins
    single_channel_entry = registry["class_based"]["algorithms"].pop("single_channel")
    registry["class_based"]["algorithms"][
        "out_of_sync_single_channel"
    ] = single_channel_entry
    # Test that an out of sync plugin causes 'create_plugin_registries' to be ran so it
    # is synced up again
    yield ("algorithms", ("single_channel",), "out_of_sync")
    reload(plugin_registry_module)
    registry = plugin_registry_module.plugin_registry.registered_plugins
    registry["class_based"]["algorithms"]["single_channel"][
        "relpath"
    ] = "some/fake/path"
    # Test that pointing a fake path to an existing plugin resets the registry and the
    # path is fixed
    yield ("algorithms", ("single_channel",), "non_existent_path")


def gen_label(val):
    """Generate the interface-plugin_name-<test_result> id for pytest."""
    return f"{val[0]}-{val[1]}-{val[2]}"


@pytest.mark.parametrize(
    "int_plug_tuple", yield_interface_plugin_tuples(), ids=gen_label
)
def test_get_plugin(int_plug_tuple):
    """Test the functionality of 'get_plugin' for the provided interface and plugin."""
    interface_name = int_plug_tuple[0]
    plugin_name = int_plug_tuple[1]
    test_result = int_plug_tuple[2]
    curr_interface = getattr(interfaces, interface_name)
    # All of these should result in a plugin getting returned. This assumes we've been
    # given a valid plugin name
    if test_result in ["normal", "out_of_sync", "non_existent_path"]:
        assert curr_interface.get_plugin(*plugin_name, rebuild_registries=True)
    # If this is in fact a plugin that does not exist, a plugin error will be raised.
    elif test_result == "no_plugin":
        with pytest.raises(PluginError):
            curr_interface.get_plugin(*plugin_name, rebuild_registries=True)
    elif test_result == "no_rebuild":
        with pytest.raises(PluginError):
            curr_interface.get_plugin(*plugin_name, rebuild_registries=False)


def test_plugin_validation_error_has_useful_message():
    """Test PluginValidationError summarizes pydantic errors instead of raw output."""
    bad_data = {
        "interface": "sectors",
        "family": "area_definition_static",
        "name": "Guam",
        "docstring": "Guam.",
        "apiVersion": "geoips/v1",
        "package": "geoips",
        "abspath": "/fake/path/guam.yaml",
        "relpath": "geoips/plugins/yaml/sectors/static/guam.yaml",
        "metadata": {
            # region contents promoted one level up -- missing the 'region' wrapper
            "area": "North",
            "city": "x",
            "continent": "Pacific",
            "country": "x",
            "state": "Guam",
            "subarea": "x",
        },
        "spec": {
            "area_id": "Guam",
            "description": "Guam.",
            "projection": {
                "a": 6371228.0,
                "lat_0": 13.4443,
                "lon_0": 144.7937,
                "proj": "eqc",
                "units": "m",
            },
            "resolution": [1000.0, 1000.0],
            "shape": {"height": 1200, "width": 1200},
            "area_extent": {
                "lower_left_xy": [-600000.0, -600000.0],
                "upper_right_xy": [600000.0, 600000.0],
            },
        },
    }

    with pytest.raises(PydanticValidationError) as pydantic_exc:
        SectorPluginModel(**bad_data)

    err = PluginValidationError(
        "Guam", "sectors", "geoips", "/fake/path.yaml", pydantic_exc.value
    )
    msg = str(err)

    assert "Guam" in msg
    assert "sectors" in msg
    assert "error(s) found" in msg
    assert len(msg.splitlines()) < len(str(pydantic_exc.value).splitlines())


def test_get_plugin_raises_plugin_validation_error_on_bad_yaml(tmp_path, monkeypatch):
    """Test get_plugin raises PluginValidationError on pydantic validation failure."""
    # Force real registry initialization BEFORE patching resources.files
    _ = interfaces.sectors.plugin_registry.registered_plugins

    # Force the pydantic path since use_pydantic is env-controlled and off by default
    monkeypatch.setattr(interfaces.sectors, "use_pydantic", True)

    bad_file = tmp_path / "bad_sector.yaml"
    bad_file.write_text("""
interface: sectors
family: area_definition_static
name: BadTestSector
docstring: Deliberately bad sector.
metadata:
  area: North  # missing 'region' wrapper
  city: x
  continent: Pacific
  country: x
  state: Guam
  subarea: x
spec:
  area_id: Guam
  description: "Guam."
  projection:
    a: 6371228.0
    lat_0: 13.4443
    lon_0: 144.7937
    proj: "eqc"
    units: "m"
  resolution: [1000.0, 1000.0]
  shape:
    height: 1200
    width: 1200
  area_extent:
    lower_left_xy: [-600000.0, -600000.0]
    upper_right_xy: [600000.0, 600000.0]
""")

    # resources.files(package) / relpath is how get_yaml_plugin builds abspath;
    # patch it to resolve to tmp_path so our file is found
    monkeypatch.setattr("geoips.plugin_registry.resources.files", lambda pkg: tmp_path)

    registry = interfaces.sectors.plugin_registry.registered_plugins
    registry.setdefault("yaml_based", {}).setdefault("sectors", {})
    registry["yaml_based"]["sectors"]["BadTestSector"] = {
        "package": "geoips",
        "relpath": "bad_sector.yaml",
    }

    try:
        with pytest.raises(PluginValidationError) as exc_info:
            interfaces.sectors.get_plugin("BadTestSector", rebuild_registries=False)
        assert "BadTestSector" in str(exc_info.value)
        assert "sectors" in str(exc_info.value)
        assert "error(s) found" in str(exc_info.value)
    finally:
        del registry["yaml_based"]["sectors"]["BadTestSector"]
