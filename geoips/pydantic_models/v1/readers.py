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
from glob import glob
import logging
import os
from pathlib import Path
from typing import Any, List

# Third-Party Libraries
from pydantic import Field, field_validator, model_validator
from pyresample.geometry import AreaDefinition
import warnings

# GeoIPS imports
from geoips.pydantic_models.v1.bases import PermissiveFrozenModel

LOG = logging.getLogger(__name__)


class ReaderArgumentsModel(PermissiveFrozenModel):
    """Reader step argument definition.

    Pydantic model defining and validating Reader step arguments.
    """

    area_def: AreaDefinition | None = Field(
        None, description="The domain over which to read data."
    )
    variables: List[str] = Field(
        None,
        description="List of variables to read",
        alias="chans",
    )
    metadata_only: bool = Field(False, description="Read metadata only.")
    self_register: str = Field(None, description="Enable self-registration.")
    fnames: List[Path] = Field(
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

    @field_validator("area_def", mode="before")
    @classmethod
    def _validate_and_normalize_areadefinition(
        cls, value: Any
    ) -> AreaDefinition | None:
        """
        Validate and normalize the input for 'area_def'.

        This method handles the input for area_def as follows:
        - 'dict': Converted to an 'AreaDefinition' object using 'create_area_def'
        - 'AreaDefinition': return 'AreaDefintion'
        - 'None' = return 'None'
        -  Other types = Raise a 'ValueError'

        Parameters
        ----------
        value: Any
            Input values for 'area_def'

        Returns
        -------
        AreaDefintion | None
            A valid 'AreaDefintion' instance or 'None'.

        Raises
        ------
        ValueError
            If the input type is other than 'AreaDefinition', 'Dict', and 'None'.
        """
        if isinstance(value, dict):
            from pyresample import create_area_def

            return create_area_def(**value)
        if value is None:
            return None
        if isinstance(value, AreaDefinition):
            return value
        raise ValueError("Input should be a valid AreaDefinition")

    @field_validator("fnames", mode="before")
    @classmethod
    def _validate_and_normalize_fnames(cls, value: Any) -> List[Path] | None:
        """
        Validate and normalize the input for 'fnames'.

        This method handles the input for fnames as follows:
        - asserts that fnames is one or more valid, existing filepaths
        - converts them to pathlib.Path objects

        Parameters
        ----------
        value: Any[PathLike]
            Input values for 'fnames'. Should be either a list of one or more strings /
            valid instances of pathlib.Path objects. Strings may contain wildcard
            characters that can be used with glob to generate a list of file paths.

        Returns
        -------
        list[PosixPath]
            A valid list of pathlib.Path objects.

        Raises
        ------
        ValueError
            If the input type is other than a list of pathlib.Path objects.
        """
        try:
            os.fspath(value)
            items = [value]
        except TypeError:
            items = value

        fnames = []

        for item in items:
            path = Path(item)

            matches = glob(str(path))
            if matches:
                fnames.extend([Path(fname) for fname in matches])
            else:
                fnames.append(path)

        if not fnames:
            raise ValueError(
                f"Error: input argument for {fnames} could not be associated with one "
                "or more existing file paths. Please ensure this data exists before "
                "continuing."
            )

        return fnames

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
        chans_message = (
            "'chans' is deprecated and will be removed in GeoIPS 2.0. Use"
            " 'variables' instead."
        )
        if "chans" in values:
            LOG.warning(chans_message)
            warnings.warn(
                chans_message,
                DeprecationWarning,
                stacklevel=2,
            )
        return values
