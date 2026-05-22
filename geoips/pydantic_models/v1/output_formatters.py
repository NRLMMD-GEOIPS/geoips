# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Pydantic models used to validate GeoIPS OBP v1 output-formatter plugins."""

# GeoIPS imports
from geoips.pydantic_models.v1.bases import PermissiveFrozenModel


class OutputFormatterArgumentsModel(PermissiveFrozenModel):
    """Filename-Formatter step argument definition.

    Pydantic model defining and validating Output Formatter step arguments.
    """

    pass
