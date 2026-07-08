# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Output formatters interface class."""

import inspect
import warnings

import xarray as xr

from geoips.interfaces.class_based_plugin import BaseClassPlugin
from geoips.interfaces.base import BaseClassInterface
from geoips.utils.types.family_conversions import OUTPUT_FORMATTER_FAMILY_CONVERSIONS


def _is_area_definition(obj):
    """Return True if *obj* looks like a pyresample Geometry (duck-typed).

    Avoids a mandatory ``pyresample`` import while still reliably detecting
    ``AreaDefinition`` / ``SwathDefinition`` objects at call time.  Only those
    classes expose the ``area_extent`` attribute.
    """
    return hasattr(obj, "area_extent") and not isinstance(obj, xr.DataTree)


class BaseOutputFormatterPlugin(BaseClassPlugin, abstract=True):
    """Base class for GeoIPS output_formatter plugins.

    Plugins with ``data_tree=False`` have their inputs / outputs
    automatically converted according to the family-specific rules
    defined in ``OUTPUT_FORMATTER_FAMILY_CONVERSIONS``.
    """

    data_tree = False
    _family_conversion_map = OUTPUT_FORMATTER_FAMILY_CONVERSIONS

    def __init_subclass__(cls, *, abstract=False, **kwargs):
        """Register a concrete output formatter subclass.

        In addition to the standard ``BaseClassPlugin`` validation this
        emits a ``DeprecationWarning`` when ``area_def`` appears before
        the data argument (``xarray_obj`` / ``xarray_dict``) in ``call``'s
        signature — the recommended order from GeoIPS 2.0 onward is data
        first, then ``area_def``.
        """
        super().__init_subclass__(abstract=abstract, **kwargs)
        if abstract or not hasattr(cls, "family") or not hasattr(cls, "call"):
            return
        sig_params = list(inspect.signature(cls.call).parameters.keys())
        data_param = next(
            (p for p in ("xarray_obj", "xarray_dict") if p in sig_params), None
        )
        if data_param and "area_def" in sig_params:
            area_idx = sig_params.index("area_def")
            data_idx = sig_params.index(data_param)
            if area_idx < data_idx:
                warnings.warn(
                    f"Output formatter {cls.name!r} (family {cls.family!r}) "
                    f"has 'area_def' before '{data_param}' in its call "
                    f"signature. The recommended order is data "
                    f"({data_param}) first, then area_def. This will "
                    f"become an error in a future release.",
                    DeprecationWarning,
                    stacklevel=2,
                )

    def _pre_call(self, data=None, *args, _obp_initiated=False, **kwargs):
        """Check argument order and reorder if necessary, then delegate.

        Two deprecation scenarios are detected:

        * **Plugin-signature order** — warned once per class at
          registration time via ``__init_subclass__``; this method
          itself does not re-detect signature ordering.

        * **Call-time argument order** — if a ``pyresample`` Geometry
          (e.g. ``AreaDefinition``) is passed as the first positional
          argument, it is moved to ``kwargs['area_def']`` and the data
          kwarg (``xarray_obj`` / ``xarray_dict``) is promoted into the
          ``data`` position.  A ``DeprecationWarning`` is emitted once
          per instance.
        """
        if data is not None and _is_area_definition(data):
            if not getattr(self, "_warned_geom_first_call", False):
                warnings.warn(
                    f"Output formatter {self.name!r} (family {self.family!r}) "
                    f"received a pyresample Geometry as the first positional "
                    f"argument. The recommended order is data first, area_def "
                    f"second.",
                    DeprecationWarning,
                    stacklevel=2,
                )
                self._warned_geom_first_call = True
            data_param = next(
                (p for p in ("xarray_obj", "xarray_dict") if p in kwargs), None
            )
            if data_param is not None:
                kwargs["area_def"] = data
                data = kwargs.pop(data_param)
        return super()._pre_call(
            data, *args, _obp_initiated=_obp_initiated, **kwargs
        )

    def _normalize_obp_kwargs(self, kwargs):
        """Rename ``output_filenames`` → ``output_fnames`` for legacy formatters.

        Legacy (family-bearing) output formatter plugins expect
        ``output_fnames`` in their ``call`` signature, but the OBP
        conduit uses ``output_filenames``.  This hook renames the kwarg
        so ``_obp_filter_kwargs`` does not drop it and ``call`` receives
        the expected argument name.

        Datatree-native output formatters (no ``family``) pass through
        unchanged.
        """
        if hasattr(self.__class__, "family") and "output_filenames" in kwargs:
            kwargs["output_fnames"] = kwargs.pop("output_filenames")
        return kwargs


class OutputFormattersInterface(BaseClassInterface):
    """Data format for the resulting output product (e.g. netCDF, png)."""

    name = "output_formatters"
    plugin_class = BaseOutputFormatterPlugin

    required_args = {
        "image": ["xarray_obj", "area_def", "product_name", "output_fnames"],
        "unprojected": ["xarray_obj", "product_name", "output_fnames"],
        "image_overlay": ["xarray_obj", "area_def", "product_name", "output_fnames"],
        "image_multi": [
            "xarray_obj",
            "area_def",
            "product_names",
            "output_fnames",
            "mpl_colors_info",
        ],
        "xrdict_area_varlist_to_outlist": ["xarray_dict", "area_def", "varlist"],
        "xrdict_area_product_outfnames_to_outlist": [
            "xarray_dict",
            "area_def",
            "product_name",
            "output_fnames",
        ],
        "xrdict_area_product_to_outlist": [
            "xarray_dict",
            "area_def",
            "product_name",
        ],
        "xrdict_to_outlist": [
            "xarray_dict",
        ],
        "xrdict_varlist_outfnames_to_outlist": [
            "xarray_dict",
            "varlist",
            "output_fnames",
        ],
        "xarray_data": ["xarray_obj", "product_names", "output_fnames"],
        "standard_metadata": [
            "xarray_obj",
            "area_def",
            "metadata_yaml_filename",
            "product_filename",
        ],
    }
    required_kwargs = {
        "image": ["product_name_title", "mpl_colors_info", "existing_image"],
        "unprojected": ["product_name_title", "mpl_colors_info"],
        "image_overlay": [
            "product_name_title",
            "clean_fname",
            "mpl_colors_info",
            "clean_fname",
            "feature_annotator",
            "gridline_annotator",
            "clean_fname",
            "product_datatype_title",
            "clean_fname",
            "bg_data",
            "bg_mpl_colors_info",
            "clean_fname",
            "bg_xarray",
            "bg_product_name_title",
            "bg_datatype_title",
            "clean_fname",
            "remove_duplicate_minrange",
        ],
        "image_multi": ["product_name_titles"],
        "xarray_dict_data": ["append", "overwrite"],
        "xarray_dict_to_image": [],
        "xarray_data": [],
        "standard_metadata": ["metadata_dir", "basedir", "output_dict"],
        "xrdict_varlist_outfnames_to_outlist": [],
        "xrdict_area_varlist_to_outlist": [],
        "xrdict_area_product_outfnames_to_outlist": [],
        "xrdict_area_product_to_outlist": [],
        "xrdict_to_outlist": [],
    }


output_formatters = OutputFormattersInterface()
