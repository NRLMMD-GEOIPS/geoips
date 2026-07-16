# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Interpolators interface class."""

import xarray as xr

from geoips.interfaces.class_based_plugin import BaseClassPlugin
from geoips.interfaces.base import BaseClassInterface


class BaseInterpolatorPlugin(BaseClassPlugin, abstract=True):
    """Base class for GeoIPS interpolator plugins."""

    data_tree = False

    def _pre_call(self, data=None, *args, _obp_initiated=False, **kwargs):
        """Prepare OBP interpolator inputs before invoking ``call``.

        Legacy interpolators expect ``area_def``, ``input_xarray``,
        ``output_xarray``, and ``varlist`` as call arguments. Under OBP, those
        values may arrive as DataTree dependencies and conduit-injected kwargs.
        Normalize them here so ``BaseClassPlugin._invoke`` can remain generic and
        still be the only method that calls ``call``.
        """
        # Workflow mode usually arrives here with a multi-input tree. Script
        # mode keeps the accumulated script tree in ``data``, then _invoke
        # extracts upstream reader/interpolator and sector nodes into conduit
        # kwargs such as ``xarray_obj`` and ``area_def``. Either shape needs
        # normalization to the legacy interpolator call signature.
        has_extracted_conduit_inputs = "xarray_obj" in kwargs or "area_def" in kwargs
        if _obp_initiated and (
            self._use_positional_unpacking(data, _obp_initiated)
            or has_extracted_conduit_inputs
        ):
            kwargs = self._prepare_obp_interpolator_kwargs(data, kwargs)
            data = super()._pre_call(
                data, *args, _obp_initiated=_obp_initiated, **kwargs
            )
            return data, kwargs

        return super()._pre_call(data, *args, _obp_initiated=_obp_initiated, **kwargs)

    def _prepare_obp_interpolator_kwargs(self, data, kwargs):
        """Populate legacy interpolator call kwargs from OBP inputs."""
        input_xarray = kwargs.pop("xarray_obj", None)
        sector_found = kwargs.get("area_def") is not None

        if input_xarray is None or not sector_found:
            input_xarray, sector_found = self._collect_interpolator_inputs(
                data, input_xarray, sector_found
            )

        if input_xarray is None:
            raise RuntimeError(
                "Error: Could not find an input dataset to interpolate for "
                f"interpolator plugin '{self.name}'."
            )

        if not sector_found:
            raise RuntimeError(
                "Error: Could not find an appropriate sector step to interpolate to for"
                f" interpolator plugin '{self.name}'."
            )

        if kwargs.get("area_def") is None:
            raise RuntimeError(
                "Error: Could not determine an appropriate area definition to "
                "interpolate to. Please ensure your interpolator step depends on a "
                "sector before continuing."
            )

        kwargs["input_xarray"] = input_xarray
        kwargs.setdefault("output_xarray", xr.Dataset())
        if kwargs.get("varlist") is None:
            kwargs["varlist"] = list(input_xarray.variables.keys())

        return kwargs

    @staticmethod
    def _collect_interpolator_inputs(data, input_xarray=None, sector_found=False):
        """Find interpolation input data and sector dependency markers."""
        if not isinstance(data, xr.DataTree):
            return input_xarray, sector_found

        for group in data.groups:
            ds = data[group]
            if not hasattr(ds, "attrs") or not ds.attrs:
                continue
            if ds.attrs.get("plugin_kind") == "sector":
                sector_found = True
            elif input_xarray is None:
                input_xarray = ds.to_dataset()

        return input_xarray, sector_found


class InterpolatorsInterface(BaseClassInterface):
    """Interpolation routine to apply when reprojecting data."""

    name = "interpolators"
    plugin_class = BaseInterpolatorPlugin

    required_args = {
        "2d": ["area_def", "input_xarray", "output_xarray", "varlist"],
        "grid": ["area_def", "input_xarray", "output_xarray", "varlist"],
    }

    required_kwargs = {"2d": ["array_num"], "grid": ["array_num"]}


interpolators = InterpolatorsInterface()
