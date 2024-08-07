"""Implementations of Pydantic base models for GeoIPS.

The pydantic base models defined here are intended for use by other base
models.

``Plugin`` should be used as the parent class of all other plugin models.

The other models defined here are intended to validate particular field types
within plugin models.
"""

from pydantic import BaseModel, constr
from typing_extensions import Annotated
from pydantic.functional_validators import AfterValidator
from matplotlib.artist import Artist
from matplotlib.lines import Line2D
from cartopy import feature


def python_identifier(val: str) -> str:
    """Validate if a string is a valid Python identifier.

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
    return val


# Create the PythonIdentifier type
PythonIdentifier = Annotated[str, AfterValidator(python_identifier)]


class Plugin(BaseModel):
    interface: PythonIdentifier
    family: PythonIdentifier
    name: PythonIdentifier
    docstring: str
    package: PythonIdentifier = None
    relpath: str = None
    abspath: str = None


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


def cartopy_feature_args(args: dict) -> dict:
    """Validate the arguments for a cartopy feature."""
    # Cartopy features are plotted using matplotlib.collections.Collection.
    # Collection plots patches. Its arguments are
    # If not enabled, just ignore everything else
    if "enabled" not in args or not args["enabled"]:
        return {"enabled": False}
    # If enabled, test the other values by instantiating lines
    # with each argument
    artist_args(args, Circle(0, radius=1))


CartopyFeatureArgs = Annotated[dict, AfterValidator(cartopy_feature_args)]


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
