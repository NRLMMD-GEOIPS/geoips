# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Pydantic models used to validate GeoIPS feature annotator plugins."""

from typing import Any, Dict, List, Literal, Optional

from pydantic import Field, model_validator

from geoips.pydantic_models.v1.bases import (
    FrozenModel,
    PluginModel,
)


class RgbEquation(FrozenModel):
    """Model for an rgb equation."""

    type: Literal["raw", "difference", "addition"] = Field(
        ..., description="The type of equation being performed."
    )
    variables: List[str] = Field(
        ..., description="The variables needed to perform the equation."
    )

    @model_validator(mode="before")
    def _validate_variables(cls, values: Dict[str, Any]) -> Dict[str, any]:
        """
        Validate that 'variables' is a valid list of strings based on the type of equation.  # NOQA

        Parameters
        ----------
        value : List[str]
            Value of the 'variables' field to validate.

        Returns
        -------
        List[str]
            Validated value of 'variables' if it is valid.

        Raises
        ------
        ValueError
            If the user-provided value for 'variables' is not valid.
        """
        variables = values.get("variables")
        if not variables:
            raise ValueError("Invalid input: 'variables' cannot be empty.")

        if len(variables) > 1 and values.get("type") == "raw":
            raise ValueError(
                "Invalid input: 'variables' cannot exceed one item when specifying "
                "type 'raw'."
            )
        elif len(variables) != 2 and values.get("type") in ["difference", "addition"]:
            raise ValueError(
                "Invalid input: 'variables' must be length two for equation type "
                "'difference' or 'addition'."
            )

        return values


class RgbGunRecipe(FrozenModel):
    """Specification for a gun of one of the r / g / b components in a rgb recipe."""

    equation: RgbEquation = Field(
        ...,
        description="The equation for a gun of an rgb recipe.",
    )
    data_range: List[float] = Field(
        ..., description="The data range for a given rgb gun."
    )
    gamma: float = Field(..., description="The gamma value for a rgb gun.")
    input_units: Optional[Literal["kelvin", "celsius", "kts", "m s-1"]] = Field(
        "kelvin",
        description="The input units of the data for the rgb gun.",
    )
    output_units: Optional[Literal["kelvin", "celsius", "kts", "m s-1"]] = Field(
        "kelvin",
        description="The input units of the data for the rgb gun.",
    )


class AlgorithmConfigSingleInstanceSpec(FrozenModel):
    """Algorithm config plugin (specification) format."""

    red: RgbGunRecipe = Field(
        ..., description="Specification for the red gun of the rgb recipe."
    )
    green: RgbGunRecipe = Field(
        ..., description="Specification for the green gun of the rgb recipe."
    )
    blue: RgbGunRecipe = Field(
        ..., description="Specification for the blue gun of the rgb recipe."
    )


class AlgorithmConfigPluginModel(PluginModel):
    """Feature Annotator plugin format."""

    spec: AlgorithmConfigSingleInstanceSpec = Field(
        ...,
        description=("Specification for algorithm config plugins."),
    )
