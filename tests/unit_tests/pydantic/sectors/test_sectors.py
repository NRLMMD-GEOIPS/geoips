"""Testing module for Pydantic SectorPluginModel."""

from copy import deepcopy
from importlib.resources import files

from pydantic import ValidationError
import pytest
import yaml

from geoips.pydantic.sectors import SectorPluginModel


class SectorDict(dict):
    """Custom dictionary class used to access Sector Plugins using paths.

    Where a 'path' is a key which can include slashes ('/') for easy access to the
    values contained in nested dictionaries.

    I.e. some_dict["key1/key2/key3"] = some_val
    """

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
    "docstring": [
        ("Local Area Sector for GeoKompsat (Korea)", "docstring_missing_period"),
        (
            "~ocal Area Sector for GeoKompsat (Korea).",
            "docstring_invalid_first_character",
        ),
    ],
    "metadata/region/continent": [(8912, "continent_invalid_type")],
    "metadata/region": [
        (
            {
                "country": "Korea",
                "area": "x",
                "subarea": "x",
                "state": "x",
                "city": "x",
            },
            "metadata_missing_continent",
        ),
    ],
    "spec": [
        (
            {
                "description": "Korea",
                "resolution": [1000, 1000],
                "shape": {"height": 1500, "width": 1500},
                "center": [0, 0],
            },
            "spec_missing_projection",
        ),
    ],
    "spec/area_id": [(8912, "area_id_invalid_type")],
    "spec/projection": [
        (
            {
                "a": 6371228.0,
                "lat_0": 37.3491,
                "lon_0": 127.5288,
                "units": "m",
            },
            "projection_missing_proj",
        )
    ],
    "spec/resolution": [([1000], "resolution_invalid_dimensions")],
    "spec/shape": [({"width": 1500}, "shape_missing_height")],
    "spec/center": [([0], "center_invalid_dimensions")],
    "spec/area_extent": [
        ({"upper_right_xy": [10000000, 10000000]}, "area_extent_missing_lower_left_xy")
    ],
    "relpath": [(None, "missing_relpath")],
    "abspath": [(None, "missing_abspath")],
    "package": [(None, "missing_package")],
}


def generate_ids(key_val):
    """Generate an ID for the key value pair provided.

    Parameters
    ----------
    key_val: tuple(str, tuple(any, str))
        - The (key, (val, val_id)) tuple to use for testing.
    """
    return key_val[1][1]


@pytest.fixture
def good_sector():
    """Return a consistent dictionary that is a valid GeoIPS sector plugin."""
    good_yaml = yaml.safe_load(
        open(str(files("geoips") / "plugins/yaml/sectors/static/korea.yaml"), mode="r")
    )
    good_yaml["abspath"] = str(
        files("geoips") / "plugins/yaml/sectors/static/korea.yaml"
    )
    good_yaml["relpath"] = "plugins/yaml/sectors/static/korea.yaml"
    good_yaml["package"] = "geoips"
    return SectorDict(deepcopy(good_yaml))


# "good_sector" is passed as a string in parametrize since indirect=True tells pytest
# to treat it as a fixture name.
@pytest.mark.parametrize(
    "good_sector",
    [pytest.param("good_sector", id="good_sector")],
    indirect=True,
)
def test_good_sector(good_sector):
    """Assert that a well formatted sector plugin is valid.

    Parameters
    ----------
    good_sector: dict
        - A dictionary representing a valid sector plugin.
    """
    SectorPluginModel(**good_sector)


def yield_key_value_pairs():
    """Yield a key value pair for bad sectors that need to be tested.

    Where the key value pair refers to the attribute to set, and the invalid value to
    set it to.
    """
    for key in list(test_cases.keys()):
        for val in test_cases[key]:
            yield (key, val)


@pytest.mark.parametrize("key_val", yield_key_value_pairs(), ids=generate_ids)
def test_bad_sector_plugins(good_sector, key_val):
    """Perform validation on static sector plugins, including failing cases.

    Parameters
    ----------
    good_sector: dict
        - A dictionary representing a sector plugin that is valid.
    key: str
        - The path to the attribute which we'll make invalid
    val: any
        - The value of an invalid attribute
    """
    bad_sector = good_sector
    key = key_val[0]
    val = key_val[1][0]
    if key in ["abspath", "relpath", "package"]:
        bad_sector.pop(key)
    else:
        bad_sector[key] = val
    if key not in ["abspath", "relpath", "package"]:
        # Package is explained below, skipping abspath and relpath until we set up
        # validation for those fields
        with pytest.raises(ValidationError):
            SectorPluginModel(**bad_sector)
    else:
        # 'package' will be automatically set by the before validation occurs. Grabbed
        # from plugin's metadata found in the registry.
        SectorPluginModel(**bad_sector)
