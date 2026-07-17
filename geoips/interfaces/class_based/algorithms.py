# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Algorithms interface class."""

import xarray as xr

from geoips.interfaces.base import BaseClassInterface
from geoips.interfaces.class_based_plugin import BaseClassPlugin
from geoips.utils.types.datatree_helpers import to_mutable_dataset
from geoips.utils.types.family_conversions import ALGORITHM_FAMILY_CONVERSIONS


class BaseAlgorithmPlugin(BaseClassPlugin, abstract=True):
    """Base class for GeoIPS algorithm plugins.

    Plugins with ``data_tree=False`` have their inputs / outputs
    automatically converted according to the family-specific rules
    defined in ``ALGORITHM_FAMILY_CONVERSIONS``.
    """

    data_tree = False
    _family_conversion_map = ALGORITHM_FAMILY_CONVERSIONS

    def _pre_call(self, data=None, *args, _obp_initiated=False, **kwargs):
        """Flatten OBP DataTree input into a mutable Dataset before base hooks.

        Algorithms that write back to ``xobj`` (e.g.
        ``xobj[product_name] = ...``) need a mutable ``xr.Dataset``. Under OBP
        upstream outputs arrive as a ``DataTree`` whose child nodes expose
        immutable ``DatasetView`` objects via ``.ds``; this override flattens
        that tree into a mutable Dataset before the base-class hook applies
        family converters. Legacy (non-OBP) inputs pass through unchanged.
        """
        if _obp_initiated and isinstance(data, xr.DataTree):
            data = to_mutable_dataset(data)
        return super()._pre_call(data, *args, _obp_initiated=_obp_initiated, **kwargs)

    def _post_call(self, data=None, *args, _obp_initiated=False, **kwargs):
        r"""Normalize algorithm output into ``DataTreeDitto`` and attach product_name.

        When invoked by the Order-Based Procflow (OBP), algorithm outputs are
        wrapped into a ``DataTreeDitto`` by the base ``_post_call`` so they can
        be stored as nodes in the workflow ``DataTree`` and retain step-level
        provenance.

        This override injects ``product_name`` into ``data.attrs`` before the
        base hook runs, ensuring downstream steps can access the resolved product
        name.

        Parameters
        ----------
        data : xr.Dataset | Any, optional
            Output produced by the algorithm. If it exposes ``.attrs``, metadata
            can be attached before wrapping.
        \*args : tuple
            Additional positional arguments forwarded to the base ``_post_call``.
        _obp_initiated : bool, default=False
            Indicates whether the call originated from the OBP workflow. When
            ``True``, output metadata is enriched and the result is wrapped for
            ``DataTree`` storage.
        \*\*kwargs : dict
            Additional keyword arguments forwarded to the base ``_post_call``.
            ``product_name`` is used here when available.

        Returns
        -------
        DataTreeDitto
            The normalized ``DataTreeDitto`` output for insertion into the workflow
            ``DataTree``.
        """
        if _obp_initiated and kwargs.get("product_name") and hasattr(data, "attrs"):
            data.attrs["product_name"] = kwargs["product_name"]
        return super()._post_call(data, *args, _obp_initiated=_obp_initiated, **kwargs)


class AlgorithmsInterface(BaseClassInterface):
    """Data manipulations to apply to the dataset."""

    name = "algorithms"
    plugin_class = BaseAlgorithmPlugin

    required_args = {
        "scalar_to_scalar": [],
        "single_channel": ["arrays"],
        "channel_combination": ["arrays"],
        "list_numpy_to_numpy": ["arrays"],
        "xarray_to_numpy": ["xobj"],
        "xarray_to_xarray": ["xobj", "variables"],  # product_name optional
        "rgb": ["arrays"],
        "xarray_dict_to_xarray": ["xarray_dict"],
        "xarray_dict_dict_to_xarray": ["xarray_dict_dict"],
        "xarray_dict_to_xarray_dict": ["xarray_dict"],
        "xarray_dict_area_def_to_numpy": ["xarray_dict", "area_def"],
    }

    required_kwargs = {
        "scalar_to_scalar": ["value"],
        "single_channel": [],
        "channel_combination": [],
        "xarray_to_numpy": [],
        "xarray_to_xarray": [],
        "list_numpy_to_numpy": [],
        "rgb": [],
        "xarray_dict_to_xarray": [],
        "xarray_dict_dict_to_xarray": [],
        "xarray_dict_to_xarray_dict": [],
        "xarray_dict_area_def_to_numpy": [],
    }


algorithms = AlgorithmsInterface()
