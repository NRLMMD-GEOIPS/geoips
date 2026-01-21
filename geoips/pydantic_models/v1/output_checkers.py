# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Pydantic models used to validate GeoIPS output checker plugins."""

from typing import List, Optional

from pydantic import Field

from geoips.pydantic_models.v1.bases import FrozenModel

class OutputCheckersArgumentsModel(FrozenModel):
    """Output Checker spec (specification) format."""

    checker_name: Optional[str] = Field(
        ..., strict=True, description="The name of the output checker."
    )
    compare_path: Optional[str] = Field(
        ..., strict=True, description="The path to the comparison file."
    )
    output_products: Optional[List[str]] = Field(
        ..., strict=True, description="A list of paths to the output file(s)."
    )
)
