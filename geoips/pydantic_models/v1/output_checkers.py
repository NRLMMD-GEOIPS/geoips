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

from pydantic import Field, model_validator

from geoips.pydantic_models.v1.bases import FrozenModel


class OutputCheckersArgumentsModel(FrozenModel):
    """Output Checker spec (specification) format."""

    checker_name: Optional[str] = Field(
        strict=True,
        description="The name of the output checker.",
    )
    compare_path: Optional[str] = Field(
        strict=True,
        description="The path to the comparison file.",
    )
    output_products: Optional[List[str]] = Field(
        strict=True,
        description="A list of paths to the output file(s).",
    )

    @model_validator(mode="after")
    def _if_checker_name_ensure_compare_path(
        self,
    ) -> OutputCheckersArgumentsModel:
        """
        Ensure compare_path is provided if checker_name is present.

        Returns
        -------
        OutputCheckersArgumentsModel
            The validated instance.

        Raises
        ------
        ValueError
            If checker_name is provided without compare_path.
        """
        if self.checker_name is not None and self.compare_path is None:
            raise ValueError(
                "A valid file path must be provided in 'compare_path' when 'checker_name' is specified."
            )

        return self
