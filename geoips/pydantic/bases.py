"""Implementations of Pydantic base models for GeoIPS.

The pydantic base models defined here are intended for use by other base
models.

``Plugin`` should be used as the parent class of all other plugin models.

The other models defined here are intended to validate particular field types
within plugin models.
"""

import keyword
from pydantic import Field, BaseModel
from typing import Tuple
from typing_extensions import Annotated
from pydantic.functional_validators import AfterValidator
from matplotlib.artist import Artist
from matplotlib.lines import Line2D

# from cartopy import feature


class PrettyBaseModel(BaseModel):
    """Make Pydantic models pretty-print by default."""

    def __str__(self):
        """Return a string representation of a Pydantic model.

        The returned string will be formatted as JSON with two-space indentation.

        Returns
        -------
            str: A string representation of the Pydantic model.
        """
        return self.model_dump_json(indent=2)


def python_identifier(val: str) -> str:
    """Validate if a string is a valid Python identifier.

    Validate if a string is a valid Python identifier and not a reserved Python keyword.
    See https://docs.python.org/3/reference/lexical_analysis.html#identifiers for more
    information on Python identifiers and reserved keywords.

    Validation is performed by calling `str.isidentifier` and `keyword.iskeyword`.

    Parameters
    ----------
        val: str
            The input string to validate.

    Returns
    -------
        str: The input string if it is a valid Python identifier.

    Raises
    ------
        ValueError: If the input string is not a valid Python identifier.
    """
    if not val.isidentifier():
        raise ValueError(f"{val} is not a valid Python identifier")
    if keyword.iskeyword(val):
        raise ValueError(f"{val} is a reserved Python keyword")
    return val


# Create the PythonIdentifier type
PythonIdentifier = Annotated[str, AfterValidator(python_identifier)]


class Plugin(PrettyBaseModel):
    """Base Plugin model for all GeoIPS plugins."""

    interface: PythonIdentifier = Field(
        description="The name of the plugin's interface."
    )
    family: PythonIdentifier = Field(description="The family of the plugin.")
    name: PythonIdentifier = Field(description="The name of the plugin.")
    # Should write a test to ensure this is a valid numpy docstring
    docstring: str = Field(description="The docstring for the plugin.")
    package: PythonIdentifier = Field(
        None, description="The package the plugin belongs to."
    )
    # Should write a test to ensure this is a valid relative path
    # Probably try instantiating pathlib.Path, then check that isabs() is False
    relpath: str = Field(None, description="The relative path to the plugin.")
    # Should write a test to ensure this is a valid relative path
    # Probably try instantiating pathlib.Path, then check that isabs() is True
    abspath: str = Field(None, description="The absolute path to the plugin.")


def mpl_artist_args(args: dict, artist: Artist) -> dict:
    """Validate the arguments for a matplotlib artist."""
    line = artist([0, 1], [0, 1])
    for key, arg in args.items():
        if key == "enabled":
            continue
        line.set(**{key: arg})
    return args


def line_args(args: dict) -> dict:
    """Validate the arguments for a matplotlib line."""
    return mpl_artist_args(args, Line2D([0, 1], [0, 1]))


LineArgs = Annotated[dict, AfterValidator(line_args)]


# def cartopy_feature_args(args: dict) -> dict:
#     """Validate the arguments for a cartopy feature."""
#     # Cartopy features are plotted using matplotlib.collections.Collection.
#     # Collection plots patches. Its arguments are the same as those for Circle.
#     # If not enabled, just ignore everything else
#     if "enabled" not in args or not args["enabled"]:
#         return {"enabled": False}
#     # If enabled, test the other values by instantiating lines
#     # with each argument
#     artist_args(args, Circle(0, radius=1))
#
#
# CartopyFeatureArgs = Annotated[dict, AfterValidator(cartopy_feature_args)]


def lat_lon_coordinate(arg: tuple[float, float]) -> tuple[float, float]:
    """Validate a latitude and longitude coordinate."""
    if arg[0] < -90 or arg[0] > 90:
        raise ValueError("Latitude must be between -90 and 90")
    if arg[1] < -180 or arg[1] > 180:
        raise ValueError("Longitude must be between -180 and 180")
    return arg


LatLonCoordinate = Annotated[Tuple[float, float], AfterValidator(lat_lon_coordinate)]


if __name__ == "__main__":
    good_plg_yaml = {
        "interface": "product",
        "family": "single",
        "name": "Infrared",
        "docstring": "Test docstring",
    }
    good_plg = Plugin(**good_plg_yaml)
    print(good_plg)

    bad_plg_yaml = {
        "interface": "product",
        "family": "single",
        "name": "Infrared-bad-name",
        "docstring": "Test docstring",
    }
    bad_plg = Plugin(**bad_plg_yaml)
