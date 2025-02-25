"""Testing module for Pydantic SectorPluginModel."""

from copy import deepcopy
from importlib.resources import files

from pydantic import ValidationError
import pytest
import yaml

from geoips.pydantic.sectors import SectorPluginModel


class SectorDict(dict):

    def __setitem__(self, key, value):
        """Set an item under key with value 'value'.

        Custom implementation of dict's __setitem__, which makes use of paths to
        set an item which may be multiple levels deep.

        Parameters
        ----------
        key: str
            - The path to the attribute to set
        value: any
            - The value to set the attribute to.
        """
        keys = key.split("/")
        if len(keys) > 1:
            current = self
            for subkey in keys[:-1]:
                current = current.setdefault(subkey, {})
            dict.__setitem__(current, keys[-1], value)
        else:
            dict.__setitem__(self, key, value)


test_cases = {
    "good_sector": "I work!",
    "docstring_missing_period": "Local Area Sector for GeoKompsat (Korea)",
    "docstring_invalid_first_character": "~ocal Area Sector for GeoKompsat (Korea).",
    "metadata/region/continent": 8912,
    "metadata/region": {
        "country": "Korea",
        "area": "x",
        "subarea": "x",
        "state": "x",
        "city": "x",
    },
    "spec": {
        "description": "Korea",
        "resolution": [1000, 1000],
        "shape": {"height": 1500, "width": 1500},
        "center": [0, 0],
    },
    "spec/area_id": 8912,
    "spec/projection": {
        "a": 6371228.0,
        "lat_0": 37.3491,
        "lon_0": 127.5288,
        "units": "m",
    },
    "spec/resolution": [1000],
    "spec/shape": {"width": 1500},
    "spec/center": [0],
    "spec/area_extent": {"upper_right_xy": [10000000, 10000000]},
    "plugin_missing_relpath": {
        "interface": "sectors",
        "family": "area_definition_static",
        "name": "korea",
        "docstring": "Local Area Sector for GeoKompsat (Korea)",
        "metadata": {
            "region": {
                "continent": "Asia",
                "country": "Korea",
                "area": "x",
                "subarea": "x",
                "state": "x",
                "city": "x",
            }
        },
        "abspath": f"{str(files('geoips') / 'plugins/yaml/sectors/static/geokompsat.yaml')}",  # NOQA
        "package": "geoips",
        "spec": {
            "area_id": "Korea",
            "description": "Korea",
            "projection": {
                "a": 6371228.0,
                "lat_0": 37.3491,
                "lon_0": 127.5288,
                "proj": "eqc",
                "units": "m",
            },
            "resolution": [1000, 1000],
            "shape": {"height": 1500, "width": 1500},
            "center": [0, 0],
        },
    },
    "plugin_missing_abspath": {
        "interface": "sectors",
        "family": "area_definition_static",
        "name": "korea",
        "docstring": "Local Area Sector for GeoKompsat (Korea)",
        "metadata": {
            "region": {
                "continent": "Asia",
                "country": "Korea",
                "area": "x",
                "subarea": "x",
                "state": "x",
                "city": "x",
            }
        },
        "relpath": "tests/unit_tests/pydantic/sectors/test_cases/good.yaml",
        "package": "geoips",
        "spec": {
            "area_id": "Korea",
            "description": "Korea",
            "projection": {
                "a": 6371228.0,
                "lat_0": 37.3491,
                "lon_0": 127.5288,
                "proj": "eqc",
                "units": "m",
            },
            "resolution": [1000, 1000],
            "shape": {"height": 1500, "width": 1500},
            "center": [0, 0],
        },
    },
    "plugin_missing_package": {
        "interface": "sectors",
        "family": "area_definition_static",
        "name": "korea",
        "docstring": "Local Area Sector for GeoKompsat (Korea)",
        "metadata": {
            "region": {
                "continent": "Asia",
                "country": "Korea",
                "area": "x",
                "subarea": "x",
                "state": "x",
                "city": "x",
            }
        },
        "abspath": f"{str(files('geoips') / 'plugins/yaml/sectors/static/geokompsat.yaml')}",  # NOQA
        "relpath": "plugins/yaml/sectors/static/geokompsat.yaml",
        "spec": {
            "area_id": "Korea",
            "description": "Korea",
            "projection": {
                "a": 6371228.0,
                "lat_0": 37.3491,
                "lon_0": 127.5288,
                "proj": "eqc",
                "units": "m",
            },
            "resolution": [1000, 1000],
            "shape": {"height": 1500, "width": 1500},
            "center": [0, 0],
        },
    },
}


@pytest.fixture
def good_sector():
    good_yaml = yaml.safe_load(
        open(str(files("geoips") / "plugins/yaml/sectors/static/korea.yaml"), mode="r")
    )
    good_yaml["abspath"] = str(
        files("geoips") / "plugins/yaml/sectors/static/korea.yaml"
    )
    good_yaml["relpath"] = "plugins/yaml/sectors/static/korea.yaml"
    good_yaml["package"] = "geoips"
    return SectorDict(deepcopy(good_yaml))


@pytest.mark.parametrize(("key", "val"), test_cases.items(), ids=test_cases.keys())
def test_sector_plugins(good_sector, key, val):
    """Perform validation on static sector plugins, including failing cases.

    Parameters
    ----------
    good_sector: dict
        - A dictionary representing a sector plugin that is valid.
    key: str
        - The path to the attribute which we'll make invalid
    val: any
        - The value of the invalid attribute
    """
    bad_sector = good_sector
    if key == "good_sector":
        SectorPluginModel(**good_sector)
        return
    elif key.startswith("docstring"):
        bad_sector["docstring"] = val
    elif key.startswith("plugin"):
        bad_sector = val
    else:
        bad_sector[key] = val
    with pytest.raises(ValidationError):
        SectorPluginModel(**bad_sector)
