# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Family-to-converter mappings for the plugin-lifecycle hooks.

Each mapping entry is a ``FamilyConversionSpec`` that tells the
``_pre_call`` / ``_post_call`` hooks what type the plugin's family
expects as input, what type it returns, and which converter functions
to use for the forward and reverse transformations.

These mappings are imported by the interface-level base classes
(``BaseAlgorithmPlugin``, ``BaseOutputFormatterPlugin``, …) via
their ``_family_conversion_map`` class attribute.
"""

from __future__ import annotations

import numpy as np
import xarray as xr

from geoips.utils.types.converters import (
    FamilyConversionSpec,
    dataset_to_dataset_dict,
    dataset_dict_to_dataset,
    dataset_vars_to_list,
    list_numpy_to_dataset,
    numpy_to_dataset,
)

# ---------------------------------------------------------------------------
# algorithm families
# ---------------------------------------------------------------------------

ALGORITHM_FAMILY_CONVERSIONS: dict[str, FamilyConversionSpec] = {
    # -- families that receive a Dataset directly ------------------------------
    "xarray_to_numpy": FamilyConversionSpec(
        input_type=xr.Dataset,
        input_converter=None,          # Dataset is what _unwrap gives
        output_type=np.ndarray,
        output_converter=numpy_to_dataset,
    ),
    "xarray_to_xarray": FamilyConversionSpec(
        input_type=xr.Dataset,
        input_converter=None,
        output_type=xr.Dataset,
        output_converter=None,         # already a Dataset
    ),
    # -- families that receive a list[np.ndarray] ------------------------------
    "list_numpy_to_numpy": FamilyConversionSpec(
        input_type=list,
        input_converter=dataset_vars_to_list,
        output_type=np.ndarray,
        output_converter=numpy_to_dataset,
    ),
    "channel_combination": FamilyConversionSpec(
        input_type=list,
        input_converter=dataset_vars_to_list,
        output_type=np.ndarray,
        output_converter=numpy_to_dataset,
    ),
    "rgb": FamilyConversionSpec(
        input_type=list,
        input_converter=dataset_vars_to_list,
        output_type=np.ndarray,
        output_converter=numpy_to_dataset,
    ),
    # -- families that receive a dict[str, Dataset] ----------------------------
    "xarray_dict_to_xarray": FamilyConversionSpec(
        input_type=dict,
        input_converter=dataset_to_dataset_dict,
        output_type=xr.Dataset,
        output_converter=None,
    ),
    "xarray_dict_dict_to_xarray": FamilyConversionSpec(
        input_type=dict,
        input_converter=dataset_to_dataset_dict,
        output_type=xr.Dataset,
        output_converter=None,
    ),
    "xarray_dict_to_xarray_dict": FamilyConversionSpec(
        input_type=dict,
        input_converter=dataset_to_dataset_dict,
        output_type=dict,
        output_converter=dataset_dict_to_dataset,
    ),
    "xarray_dict_area_def_to_numpy": FamilyConversionSpec(
        input_type=dict,
        input_converter=dataset_to_dataset_dict,
        output_type=np.ndarray,
        output_converter=numpy_to_dataset,
    ),
    # -- scalar family ---------------------------------------------------------
    "scalar_to_scalar": FamilyConversionSpec(
        input_type=xr.Dataset,
        input_converter=None,
        output_type=(int, float),
        output_converter=None,
    ),
}

# ---------------------------------------------------------------------------
# output-formatter families
# ---------------------------------------------------------------------------

OUTPUT_FORMATTER_FAMILY_CONVERSIONS: dict[str, FamilyConversionSpec] = {
    # -- families that receive a single Dataset --------------------------------
    "image": FamilyConversionSpec(
        input_type=xr.Dataset,
        input_converter=None,
        output_type=xr.Dataset,
        output_converter=None,
    ),
    "unprojected": FamilyConversionSpec(
        input_type=xr.Dataset,
        input_converter=None,
        output_type=xr.Dataset,
        output_converter=None,
    ),
    "image_overlay": FamilyConversionSpec(
        input_type=xr.Dataset,
        input_converter=None,
        output_type=xr.Dataset,
        output_converter=None,
    ),
    "image_multi": FamilyConversionSpec(
        input_type=xr.Dataset,
        input_converter=None,
        output_type=xr.Dataset,
        output_converter=None,
    ),
    "xarray_data": FamilyConversionSpec(
        input_type=xr.Dataset,
        input_converter=None,
        output_type=xr.Dataset,
        output_converter=None,
    ),
    "standard_metadata": FamilyConversionSpec(
        input_type=xr.Dataset,
        input_converter=None,
        output_type=xr.Dataset,
        output_converter=None,
    ),
    # -- families that receive a dict[str, Dataset] ----------------------------
    "xrdict_varlist_outfnames_to_outlist": FamilyConversionSpec(
        input_type=dict,
        input_converter=dataset_to_dataset_dict,
        output_type=dict,
        output_converter=dataset_dict_to_dataset,
    ),
    "xrdict_area_product_outfnames_to_outlist": FamilyConversionSpec(
        input_type=dict,
        input_converter=dataset_to_dataset_dict,
        output_type=dict,
        output_converter=dataset_dict_to_dataset,
    ),
    "xrdict_area_product_to_outlist": FamilyConversionSpec(
        input_type=dict,
        input_converter=dataset_to_dataset_dict,
        output_type=dict,
        output_converter=dataset_dict_to_dataset,
    ),
    "xrdict_to_outlist": FamilyConversionSpec(
        input_type=dict,
        input_converter=dataset_to_dataset_dict,
        output_type=dict,
        output_converter=dataset_dict_to_dataset,
    ),
    "xrdict_area_varlist_to_outlist": FamilyConversionSpec(
        input_type=dict,
        input_converter=dataset_to_dataset_dict,
        output_type=dict,
        output_converter=dataset_dict_to_dataset,
    ),
}


# ---------------------------------------------------------------------------
# helper — applies the conversion spec from within a hook
# ---------------------------------------------------------------------------


def apply_pre_conversion(
    data: object,
    family: str,
    conversions_map: dict[str, FamilyConversionSpec],
) -> object:
    """Apply the input-side conversion for *family*.

    Parameters
    ----------
    data : Any
        Native object (already unwrapped from DataTreeDitto).
    family : str
        Plugin family name.
    conversions_map : dict[str, FamilyConversionSpec]
        The family-to-spec mapping for the interface.

    Returns
    -------
    Any
        Converted data, or *data* unchanged if no converter is defined.
    """
    spec = conversions_map.get(family)
    if spec is None or spec.input_converter is None:
        return data
    if spec.input_type is not None and isinstance(data, spec.input_type):
        return data
    return spec.input_converter(data)


def apply_post_conversion(
    data: object,
    family: str,
    conversions_map: dict[str, FamilyConversionSpec],
) -> object:
    """Apply the output-side conversion for *family*.

    Parameters
    ----------
    data : Any
        Plugin return value.
    family : str
        Plugin family name.
    conversions_map : dict[str, FamilyConversionSpec]
        The family-to-spec mapping for the interface.

    Returns
    -------
    Any
        Converted data (typically an ``xr.Dataset``), or *data*
        unchanged if no converter is defined.
    """
    spec = conversions_map.get(family)
    if spec is None or spec.output_converter is None:
        return data
    if spec.output_type is not None and isinstance(data, spec.output_type):
        return data
    return spec.output_converter(data)
