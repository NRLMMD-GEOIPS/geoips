# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Validators interface module."""

from geoips.interfaces.base import BaseClassInterface


class ValidatorsInterface(BaseClassInterface):
    """Interface for plugins validating data against a source of truth."""

    name = "validators"

    required_args = {"standard": ["xarray_obj", "truth_xarray_obj"]}
    required_kwargs = {"standard": {}}
    allowable_kwargs = {"standard": {"vars_to_validate"}}


validators = ValidatorsInterface()
