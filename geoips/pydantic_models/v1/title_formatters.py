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
    product_name_title: str = Field(None, description="Product name title.")
    product_datatype_title: str = Field(
        None, description="Product data type label to incude in the title."
    )
    bg_product_name_title: str = Field(
        None,
        description="Background product name title when background layer is provided.",
    )
    bg_datatype_title: str = Field(
        None, description="Background data type label for the background product title."
    )
    title_copyright: str = Field(
        None, description="Copyright string to append to the generated title"
    )
