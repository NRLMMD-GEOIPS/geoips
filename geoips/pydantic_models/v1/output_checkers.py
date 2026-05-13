# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Pydantic models used to validate GeoIPS output checker plugins."""

# Previously, the model names used as type hints were quoted marking them as strings;
# leading to forward references, which allow referring to a class before Python has
# fully parsed it.

# By adding from __future__ import annotations, Python defers evaluation of all type
# annotations until runtime, automatically treating them as strings. This eliminates
# the need to manually quote forward-referenced types (simplified type hinting).
from __future__ import annotations

from typing import List, Optional

from pydantic import Field, FilePath

from geoips.pydantic_models.v1.bases import FrozenModel


class OutputCheckerArgumentsModel(FrozenModel):
    """Output Checker spec (specification) format."""

    compare_path: Optional[FilePath] = Field(
        strict=True,
        description="The path to the comparison file.",
    )
    output_products: Optional[List[FilePath]] = Field(
        strict=True,
        description="A list of paths to the output file(s).",
    )
