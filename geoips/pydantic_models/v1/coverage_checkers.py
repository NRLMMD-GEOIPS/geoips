# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Pydantic models used to validate GeoIPS OBP v1 coverage-checker plugins."""


# Python Standard Libraries
# from typing import Optional, Self
from typing import Optional

# Third-Party Libraries
# from pydantic import Field, model_validator
from pydantic import Field

# GeoIPS imports
from geoips.pydantic_models.v1.bases import PermissiveFrozenModel


class CoverageCheckerArgumentsModel(PermissiveFrozenModel):
    """Coverage-Checker step argument definition.

    Pydantic model defining and validating Coverage Checker step arguments.
    """

    variable_name: str = Field(
        None, description="Variable name to check percent unmasked."
    )
    area_def: str = Field(None, description="Area definition identifier.")
    radius_km: Optional[int] = Field(
        300, description="Radius of center disk to check for coverage. "
    )
