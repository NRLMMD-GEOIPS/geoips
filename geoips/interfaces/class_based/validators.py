# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Validators interface module."""

from geoips.interfaces.base import BaseClassInterface
from geoips.interfaces.class_based_plugin import BaseClassPlugin


class BaseValidatorPlugin(BaseClassPlugin, abstract=True):
    """Base class for GeoIPS validator plugins."""

    pass


class ValidatorsInterface(BaseClassInterface):
    """Interface for plugins validating data against a source of truth."""

    name = "validators"
    plugin_class = BaseValidatorPlugin
    required_args = {"standard": ["xarray_obj", "truth_xarray_obj"]}
    required_kwargs = {"standard": {}}
    allowable_kwargs = {"standard": {"vars_to_validate"}}


validators = ValidatorsInterface()
