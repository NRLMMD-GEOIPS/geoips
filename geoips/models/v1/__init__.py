# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""GeoIPS order-based procflow pydantic models init file."""

import importlib
import pkgutil
import inspect

_modules = {}
_classes = {}

for _, modname, _ in pkgutil.iter_modules(__path__):
    full_name = f"{__name__}.{modname}"
    module = importlib.import_module(full_name)
    _modules[full_name] = module

    _classes[full_name] = [
        name for name, obj in inspect.getmembers(module, inspect.isclass)
        if obj.__module__ == full_name
    ]
