# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Pydantic models used to validate GeoIPS output checker plugins."""

from __future__ import annotations

from typing import List, Optional

from pydantic import Field, model_validator

from geoips.pydantic_models.v1.bases import FrozenModel

from ipdb import set_trace as shell


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
    def _validate_compare_path_against_checker_name(
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
                "'compare_path' must be provided when 'checker_name' is set."
            )

        return self
