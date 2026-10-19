# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Output formatters base interface class."""


import xarray as xr

import inspect
import logging


LOG = logging.getLogger(__name__)

DATA_PARAM_NAMES = ("xarray_obj", "xarray_dict")

def _is_area_definition(obj):
    """Return True if *obj* looks like a pyresample Geometry (duck-typed).

    Avoids a mandatory ``pyresample`` import while still reliably detecting
    ``AreaDefinition`` / ``SwathDefinition`` objects at call time.  Only those
    classes expose the ``area_extent`` attribute.
    """
    return hasattr(obj, "area_extent") and not isinstance(obj, xr.DataTree)


def _call_with_original_order(call_method, original_params, self_obj, bound_args):
    """Call a legacy implementation using its original parameter order."""
    args = [self_obj]
    kwargs = {}
    for param in original_params[1:]:
        if param.name not in bound_args.arguments:
            continue
        value = bound_args.arguments[param.name]
        if param.kind is inspect.Parameter.POSITIONAL_ONLY:
            args.append(value)
        elif param.kind is inspect.Parameter.VAR_POSITIONAL:
            args.extend(value)
        elif param.kind is inspect.Parameter.VAR_KEYWORD:
            kwargs.update(value)
        else:
            kwargs[param.name] = value
    return call_method(*args, **kwargs)