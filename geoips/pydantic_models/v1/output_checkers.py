# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Pydantic models used to validate GeoIPS output checker plugins."""

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
    def _validate_output_checker_path(
        cls, model: OutputCheckersArgumentsModel
    ) -> OutputCheckersArgumentsModel:
        """
        Ensure the Output Checker contains a compare_path if checker_name is present.

        Parameters
        ----------
        model: OutputCheckersArgumentsModel
            The OutputCheckersArgumentsModel instance to validate.

        Returns
        -------
        OutputCheckersArgumentsModel
            The validated instance of OutputCheckersArgumentsModel

        Raises
        ------
        ValueError
            If the plugin name is not valid for the specified plugin kind.
        """
        shell()
        return model