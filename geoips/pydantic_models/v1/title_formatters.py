# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Pydantic models used to validate GeoIPS OBP v1 title-formatter plugins."""

# Third-Party Libraries
from pydantic import Field

# GeoIPS imports
from geoips.pydantic_models.v1.bases import PermissiveFrozenModel


class TitleFormatterArgumentsModel(PermissiveFrozenModel):
    """Title-Formatter step argument definition.

    Pydantic model defining and validating Title Formatter step arguments.
    """

    area_def: str = Field(None, description="Area definition identifier.")
    product_name_title: str = Field(..., description="Area definition identifier.")
    product_datatype_title: str = Field(None, description="TBA.")
    bg_product_name_title: str = Field(None, description="TBA.")
    bg_datatype_title: str = Field(None, description="TBA.")
    title_copyright: str = Field(None, description="TBA.")
