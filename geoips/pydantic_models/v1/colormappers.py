# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Pydantic models used to validate GeoIPS OBP v1 colormapper plugins."""

# GeoIPS imports
from geoips.pydantic_models.v1.bases import PermissiveFrozenModel


class ColormapperArgumentsModel(PermissiveFrozenModel):
    """Colormapper step argument definition.

    Pydantic model defining and validating Colormapper step arguments.
    """

    pass
