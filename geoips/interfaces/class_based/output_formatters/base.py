# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Output formatters base interface class."""


import xarray as xr

import inspect
import logging
import functools
import warnings


from geoips.errors import BoundaryIOError
from geoips.geoips_utils import replace_geoips_paths
from geoips.interfaces.base import BaseClassInterface
from geoips.utils.types.family_conversions import OUTPUT_FORMATTER_FAMILY_CONVERSIONS
from geoips.interfaces.class_based_plugin import BaseClassPlugin



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
        legacy_area_first = False
        if not abstract and "call" in cls.__dict__:
            cls.call, legacy_area_first = _normalize_output_formatter_call_signature(
                cls.__dict__["call"]
            )

        super().__init_subclass__(abstract=abstract, **kwargs)
        if abstract or not hasattr(cls, "family") or not hasattr(cls, "call"):
            return
        if legacy_area_first:
            data_param = next(
                pname
                for pname in DATA_PARAM_NAMES
                if pname in inspect.signature(cls.call).parameters
            )
            warnings.warn(
                f"Output formatter {cls.name!r} (family {cls.family!r}) "
                f"has a legacy 'area_def' before '{data_param}' implementation "
                f"signature. GeoIPS will expose and invoke it as data-first "
                f"({data_param}) first, then area_def. "
                f"The preferred migration is to make this plugin "
                f"DataTree-native (set ``data_tree = True`` and "
                f"remove ``family``).",
                DeprecationWarning,
                stacklevel=2,
            )

    def _normalize_call_args(self, data, args, kwargs, *, _obp_initiated=False):
        """Normalize legacy formatter calls to data-first argument order.

        Legacy procflows may call output formatters as either
        ``formatter(area_def, xarray_obj, ...)`` or
        ``formatter(area_def, xarray_obj=xarray_obj, ...)``.  Normalize both
        forms to the data-first convention exposed by ``call``:
        ``formatter(xarray_obj, area_def, ...)``.
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
                (p for p in DATA_PARAM_NAMES if p in kwargs),
                None,
            )
            if data_param is None and args:
                return args[0], (data, *args[1:]), kwargs
            if data_param is not None:
                new_kwargs = dict(kwargs)
                new_data = new_kwargs.pop(data_param)
                return new_data, (data, *args), new_kwargs
        return super()._normalize_call_args(
            data, args, kwargs, _obp_initiated=_obp_initiated
        )

    def _pre_call(self, data=None, *args, _obp_initiated=False, **kwargs):
        """Check argument order and reorder if necessary, then delegate.

        Under OBP, bridges the singular ``product_name`` global to the
        ``product_names`` list expected by output formatter ``call()`` methods.
        """
        if (
            _obp_initiated
            and "product_names" not in kwargs
            and "product_name" in kwargs
        ):
            kwargs["product_names"] = [kwargs["product_name"]]
            result = super()._pre_call(
                data, *args, _obp_initiated=_obp_initiated, **kwargs
            )
            return result, kwargs
        return super()._pre_call(data, *args, _obp_initiated=_obp_initiated, **kwargs)

    def _post_call(self, data, *args, _obp_initiated=False, **kwargs):
        """Attach semantic output-file attrs to OBP output formatter results."""
        if not (_obp_initiated and isinstance(data, list)):
            return super()._post_call(
                data, *args, _obp_initiated=_obp_initiated, **kwargs
            )

        if not data:
            raise BoundaryIOError(
                f"Output formatter plugin '{self.name}' did not produce any "
                "output products."
            )

        output_products = list(data)
        data = super()._post_call(
            data,
            *args,
            _obp_initiated=_obp_initiated,
            **kwargs,
        )

        attrs = (
            data.ds.attrs
            if isinstance(data, xr.DataTree) and data.ds is not None
            else None
        )
        if attrs is not None:
            attrs.setdefault("output_products", output_products)

        return data

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

    def update_sector_info_with_default_metadata(
        self, area_def, xarray_obj, product_filename=None, metadata_filename=None
    ):
        """Update sector info found in "area_def" with standard metadata output.

        This function is used by metadata_tc output formatter as well for updating the
        sector_info with these additional default metadata fields. We should not filter
        out non-default metadata here, since metadata_tc uses this function.

        Parameters
        ----------
        area_def : AreaDefinition
            Pyresample AreaDefinition of sector information
        xarray_obj : xarray.Dataset
            xarray Dataset object that was used to produce product
        product_filename : str
            Full path to full product filename that this YAML file refers to

        Returns
        -------
        dict
            sector_info dict with standard metadata added
             * bounding box
             * product filename with wildcards
             * basename of original source filenames
        """
        sector_info = area_def.sector_info.copy()

        if hasattr(area_def, "sector_type") and "sector_type" not in sector_info:
            sector_info["sector_type"] = area_def.sector_type

        sector_info["bounding_box"] = {}
        sector_info["bounding_box"]["minlat"] = area_def.area_extent_ll[1]
        sector_info["bounding_box"]["maxlat"] = area_def.area_extent_ll[3]
        sector_info["bounding_box"]["minlon"] = area_def.area_extent_ll[0]
        sector_info["bounding_box"]["maxlon"] = area_def.area_extent_ll[2]
        sector_info["bounding_box"]["pixel_width_m"] = area_def.pixel_size_x
        sector_info["bounding_box"]["pixel_height_m"] = area_def.pixel_size_y
        sector_info["bounding_box"]["image_width"] = area_def.width
        sector_info["bounding_box"]["image_height"] = area_def.height
        sector_info["bounding_box"]["proj4_string"] = area_def.proj_str

        if product_filename:
            sector_info["product_filename"] = replace_geoips_paths(product_filename)
        if metadata_filename:
            sector_info["metadata_filename"] = replace_geoips_paths(metadata_filename)

        if "source_file_names" in xarray_obj.attrs.keys():
            sector_info["source_file_names"] = xarray_obj.source_file_names
        # Backwards compatibility, so the default metadata doesn't change.

        return sector_info


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
