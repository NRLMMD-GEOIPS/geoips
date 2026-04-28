# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Pydantic models used to validate GeoIPS OBP v1 reader plugins."""

# Previously, the model names used as type hints were quoted marking them as strings;
# leading to forward references, which allow referring to a class before Python has
# fully parsed it.

# By adding from __future__ import annotations, Python defers evaluation of all type
# annotations until runtime, automatically treating them as strings. This eliminates
# the need to manually quote forward-referenced types (simplified type hinting).
from __future__ import annotations

# Python Standard Libraries
import logging
from typing import List

# Third-Party Libraries
from pydantic import Field, model_validator
from pyresample.geometry import AreaDefinition

# GeoIPS imports
from geoips.pydantic_models.v1.bases import PermissiveFrozenModel

LOG = logging.getLogger(__name__)


class ReaderArgumentsModel(PermissiveFrozenModel):
    """Reader step argument definition.

    Pydantic model defining and validating Reader step arguments.
    """

    area_def: AreaDefinition = Field(None, description="Area definition identifier.")
    variables: List[str] = Field(
        None,
        description="List of channels to process",
        alias="chans",
    )
    metadata_only: bool = Field(False, description="Read metadata only.")
    self_register: str = Field(None, description="Enable self-registration.")
    fnames: List[str] = Field(
        None, description="full path to the file(s) for static dataset inputs."
    )
    sectored_read: bool = Field(False)
    self_register_source: str = Field(
        None, description="Source dataset to use for self-registration"
    )
    self_register_dataset: str = Field(
        None, description="Dataset within the source to use for self-registration"
    )
    resampled_read: bool = Field(
        False,
        description="Specify whether a resampled read is required, needed for "
        "datatypes that will be read within 'get_alg_xarray'",
    )

    @model_validator(mode="before")
    def _handle_deprecated_chans(cls, values):
        """
        Check for the deprecated 'chans' field and issue a warning.

        This method detects if `chans` is present in the input values and issues a
        deprecation warning, recommending the use of 'variable' instead.

        Parameters
        ----------
        values : dict
            Input values to the model.

        Returns
        -------
        dict
            The original input values.
        """
        if "chans" in values:
            LOG.warning(
                "'chans' is deprecated and will be removed in GeoIPS 2.0. Use"
                "'variables' instead."
            )
        return values
