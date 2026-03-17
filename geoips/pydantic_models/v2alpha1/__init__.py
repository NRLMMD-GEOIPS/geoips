# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""GeoIPS order-based procflow v2alpha1 models init file."""

import logging
import importlib
import inspect
import pkgutil
import sys

LOG = logging.getLogger(__name__)


# This function is required to dynamically load versioned models in the unit tests
# Due for further refactoring and optimization in the upcoming PR
# Relevant issue : https://github.com/NRLMMD-GEOIPS/geoips/issues/1125
def collect_modules():
    """Dynamically find and import all submodules within a package."""
    modules = {}

    # Get the current package (i.e., geoips.pydantic_models)
    package = sys.modules[__name__]

    for _, module_name, is_pkg in pkgutil.walk_packages(  # NOQA
        package.__path__, package.__name__ + "."
    ):
        try:
            module = importlib.import_module(module_name)
            modules[module_name] = module
        except ImportError as e:
            LOG.warning(f"Could not import {module_name}: {e}")

    return modules


# This function is required to dynamically load versioned models in the unit tests
# Due for further refactoring and optimization in the upcoming PR
# Relevant issue : https://github.com/NRLMMD-GEOIPS/geoips/issues/1125
def collect_classes(modules):
    """Extract all classes from the given modules.

    Parameters
    ----------
    modules: dict
        - A dictionary of mod_name: module objects found within geoips.pydantic
    """
    classes = {}

    for module_name, module in modules.items():
        module_classes = {
            name: cls
            for name, cls in inspect.getmembers(module, inspect.isclass)
            if cls.__module__
            == module_name  # Ensure it's defined in the module, not imported
        }
        if module_classes:
            classes[module_name] = module_classes

    return classes


_modules = collect_modules()
_classes = collect_classes(_modules)  # NOQA
