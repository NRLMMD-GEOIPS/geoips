# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Filename formatters interface class."""

import xarray as xr

from geoips.interfaces.class_based_plugin import BaseClassPlugin
from geoips.interfaces.base import BaseClassInterface


class BaseFilenameFormatterPlugin(BaseClassPlugin, abstract=True):
    """Base class for GeoIPS filename_formatter plugins."""

    data_tree = False

    def _pre_call(self, data=None, *args, _obp_initiated=False, **kwargs):
        r"""Normalize ``DataTreeDitto`` input into a mutable ``xr.Dataset``.

        When invoked by OBP, upstream dependency outputs are collected into a
        multi-input ``xr.DataTree``. This hook converts the child node datasets into a
        writable ``xr.Dataset`` so ``call()`` receives the expected ``xarray_obj``
        input.

        A single upstream dependency is converted directly. Multiple upstream
        dependencies are merged into one dataset.

        Parameters
        ----------
        data : xr.DataTree | xr.Dataset | None, optional
            Upstream input passed into the plugin. In OBP, this is typically a
            multi-input ``xr.DataTree`` containing dependency nodes.
        \*args : tuple
            Additional positional arguments forwarded to the base ``_pre_call``.
        _obp_initiated : bool, default=False
            Indicates whether the call originated from OBP.
        \*\*kwargs : dict
            Additional keyword arguments forwarded to the base ``_pre_call``.

        Returns
        -------
        xr.Dataset | Any
            A mutable ``xr.Dataset`` when upstream ``xr.DataTree`` input is
            normalized; otherwise the result returned by the base ``_pre_call``.
        """
        if _obp_initiated and isinstance(data, xr.DataTree):
            data = self._to_mutable_dataset(data)
        return super()._pre_call(
            data, *args, _obp_initiated=_obp_initiated, **kwargs
        )

    def _post_call(self, data=None, *args, _obp_initiated=False, **kwargs):
        r"""Normalize filename output into ``DataTreeDitto`` for OBP.

        Filename formatter ``call()`` methods return a plain output path string. When
        invoked by OBP, this hook wraps that path into a ``DataTreeDitto`` so it can be
        attached to the workflow ``DataTree`` with metadata needed by downstream steps.

        Parameters
        ----------
        data : str | None
            The output filename produced by ``call()``.
        _obp_initiated : bool, default=False
            Indicates whether the call originated from OBP. When ``True``,
            the filename is wrapped into ``DataTreeDitto``.

        Returns
        -------
        DataTreeDitto | str | None
            The normalized ``DataTreeDitto`` output for insertion into the workflow
            ``DataTree``.
        """
        if _obp_initiated and isinstance(data, str):
            import xarray as xr
            from geoips.utils.types.datatree_ditto import DataTreeDitto

            ds = xr.Dataset(
                {"output_path": (["path"], [data])},
                attrs={
                    "output_fnames": [data],
                    "plugin_kind": "filename_formatter",
                    "output_key": "output_fnames",
                },
            )
            return DataTreeDitto(ds, name="filename_output")
        return data


class FilenameFormattersInterface(BaseClassInterface):
    """Specification for formatting the full path and file name.

    File path and name formatting is determined using attributes within the
    GeoIPS xarray objects.
    """

    name = "filename_formatters"
    plugin_class = BaseFilenameFormatterPlugin

    required_args = {
        "standard": ["area_def", "xarray_obj", "product_name"],
        "xarray_metadata_to_filename": ["xarray_obj"],
        "data": ["area_def", "xarray_obj", "product_names"],
        "standard_metadata": ["area_def", "xarray_obj", "product_filename"],
        "xarray_area_product_to_filename": ["xarray_obj", "area_def", "product_name"],
    }
    required_kwargs = {
        "standard": [
            "coverage",
            "output_type",
            "basedir",
        ],
        "xarray_metadata_to_filename": ["extension", "basedir"],
        "data": [
            "coverage",
            "output_type",
            "basedir",
        ],
        "standard_metadata": ["metadata_dir", "metadata_type", "basedir"],
        "xarray_area_product_to_filename": ["output_type", "basedir", "extra_field"],
    }

    # The functions below were commented out as they included errors, and were not used
    # by GeoIPS at this time. 9/27/23

    # def find_duplicates(self, *args, **kwargs):
    #     """Find duplicate files."""
    #     try:
    #         func = self.get_plugin_attr(name, "find_duplicates")
    #     except AttributeError:
    #         raise AttributeError(
    #             f'Plugin {name} does not have a "find_duplicates" function.'
    #         )

    #     duplicates = func()

    # def remove_duplicates(self):
    #     """Remove duplicate files."""
    #     duplicates = self.find_duplicates()


filename_formatters = FilenameFormattersInterface()
