# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Output formatters base interface class."""


import xarray as xr

import inspect
import logging
import functools



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


def _normalize_output_formatter_call_signature(call_method):
    """Return a data-first wrapper for legacy area-first output formatters."""
    original_sig = inspect.signature(call_method)
    original_params = list(original_sig.parameters.values())
    param_names = [param.name for param in original_params]

    data_param_name = next(
        (pname for pname in DATA_PARAM_NAMES if pname in param_names), None
    )
    if data_param_name is None or "area_def" not in param_names:
        return call_method, False

    data_idx = param_names.index(data_param_name)
    area_idx = param_names.index("area_def")
    if data_idx < area_idx:
        return call_method, False

    insert_idx = 1 if param_names and param_names[0] == "self" else 0
    data_param = original_params[data_idx]
    normalized_params = [
        param for idx, param in enumerate(original_params) if idx != data_idx
    ]
    normalized_params.insert(insert_idx, data_param)
    normalized_sig = original_sig.replace(parameters=normalized_params)

    @functools.wraps(call_method)
    def _data_first_call(self, *args, **kwargs):
        if args and _is_area_definition(args[0]):
            return call_method(self, *args, **kwargs)
        bound_args = normalized_sig.bind(self, *args, **kwargs)
        return _call_with_original_order(call_method, original_params, self, bound_args)

    _data_first_call.__signature__ = normalized_sig
    return _data_first_call, True
