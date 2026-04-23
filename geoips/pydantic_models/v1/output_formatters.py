# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Pydantic models used to validate GeoIPS OBP v1 output-formatter plugins."""

# Third-Party Libraries
from pydantic import Field

# GeoIPS imports
from geoips.pydantic_models.v1.bases import FrozenModel, PermissiveFrozenModel


class MatplotlibBasedCommonImageryArgumentsModel(FrozenModel):
    """Arguments common to output imagery generated using Matplotlib."""

    feature_annotator: str | None = Field(None)


class OutputFormatterArgumentsModel(PermissiveFrozenModel):
    """Output-Formatter step argument definition.

    Pydantic model defining and validating Output Formatter step arguments.
    """

    product_name_title: str = Field(None, description="TBA")
