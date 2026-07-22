# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Filename formatters interface class."""

from os.path import join as pathjoin

import xarray as xr

from geoips.interfaces.base import BaseClassInterface
from geoips.interfaces.class_based_plugin import BaseClassPlugin
from geoips.utils.types.datatree_ditto import DataTreeDitto
from geoips.utils.types.datatree_helpers import to_mutable_dataset


class BaseFilenameFormatterPlugin(BaseClassPlugin, abstract=True):
    """Base class for GeoIPS filename_formatter plugins."""

    data_tree = False

    def _normalize_obp_kwargs(self, kwargs):
        """Default ``area_def`` to ``None`` when no sector step is upstream.

        Filename formatters that accept ``area_def`` (e.g. ``basic_fname``)
        guard against ``None`` with an ``if area_def:`` check, so ``None`` is
        a valid sentinel meaning "no area definition available". When no sector
        step is listed in ``depends_on`` the conduit never injects ``area_def``,
        so we default it here rather than requiring every unsectored workflow to
        repeat ``arguments: {area_def: null}``.
        """
        kwargs.setdefault("area_def", None)
        return kwargs

    def _pre_call(self, data=None, *args, _obp_initiated=False, **kwargs):
        """Flatten OBP DataTree input into a mutable Dataset before base hooks.

        Under OBP, upstream dependency outputs are collected into a multi-input
        ``xr.DataTree``. This override flattens the child node datasets into a
        writable ``xr.Dataset`` so ``call()`` receives the expected
        ``xarray_obj`` input. Legacy (non-OBP) inputs pass through unchanged.

        Also bridges the singular ``product_name`` global (OBP convention) to
        the ``product_names`` list expected by ``data``-family formatters.
        """
        kwargs_modified = False
        if _obp_initiated:
            if isinstance(data, xr.DataTree):
                data = to_mutable_dataset(data)
            if "product_names" not in kwargs and "product_name" in kwargs:
                kwargs["product_names"] = [kwargs["product_name"]]
                kwargs_modified = True
        result = super()._pre_call(data, *args, _obp_initiated=_obp_initiated, **kwargs)
        if kwargs_modified:
            return result, kwargs
        return result

    def _post_call(self, data=None, *args, _obp_initiated=False, **kwargs):
        r"""Normalize filename output into ``DataTreeDitto`` for OBP.

        Filename formatter ``call()`` methods return a plain output path string. When
        invoked by OBP, this hook wraps that path into a ``DataTreeDitto`` so it can be
        attached to the workflow ``DataTree`` with metadata needed by downstream steps.

        Why a data variable and not just ``attrs``? The output path *is* this
        step's produced data, so it is stored as an ``output_path`` data
        variable (a ``DataArray``). Plugin kinds whose product is purely
        descriptive (e.g. a sector's area definition, a colormapper's color
        info) carry that information in ``attrs`` instead, because it describes
        the node rather than being the node's data. The path is additionally
        mirrored into ``attrs['output_filenames']`` for the conduit that feeds it
        to downstream steps.

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
            ds = xr.Dataset(
                {"output_path": (["path"], [data])},
                attrs={
                    "output_filenames": [data],
                    "plugin_kind": "filename_formatter",
                    "output_key": "output_filenames",
                },
            )
            return DataTreeDitto(ds, name="filename_output")
        return data


class WindsFilenameFormatterPlugin(BaseFilenameFormatterPlugin, abstract=True):
    """Base class for wind-based filename_formatter plugins."""

    def assemble_windspeeds_text_full_fname(
        self,
        basedir,
        source_name,
        platform_name,
        data_provider,
        product_datetime,
        dt_format="%Y%m%d.%H%M",
        extension=".txt",
        creation_time=None,
    ):
        """Produce full output product path using product / sensor specifications.

        Parameters
        ----------
        basedir : str
             base directory
        source_name : str
            Name of source (sensor)
        platform_name : str
            Name of platform (satellite)
        data_provider : str
            Name of data provider
        product_datetime : datetime.datetime
            Start time of data used to generate product
        dt_format : str, default="%Y%m%d.%H%M"
            Format used to display product_datetime within filename
        extension : str, default=".txt"
            File extension, specifying type.
        creation_time : datetime.datetime, default=None
            Include given creation_time of file in filename
            If None, do not include creation time.

        Returns
        -------
        str
            full path of output filename of the format:
              <basedir>/<source_name>_<data_provider>_<platform_name>_
              surface_winds_<YYYYMMDDHHMN>

        Examples
        --------
        >>> startdt = datetime.strptime('20200216T001412', '%Y%m%dT%H%M%S')
        >>> assemble_windspeeds_text_full_fname(
        ...     '/outdir',
        ...     'smap-spd',
        ...     'smap',
        ...     'remss',
        ...     startdt,
        ...     '%Y%m%d'
        ...     )
        '/outdir/smap-spd_remss_smap_surface_winds_20200216'
        """
        fname = "_".join(
            [
                source_name,
                data_provider,
                platform_name,
                "surface_winds",
                product_datetime.strftime(dt_format),
            ]
        )

        if creation_time is not None:
            fname = fname + "_creationtime_" + creation_time.strftime("%Y%m%dT%H%MZ")

        if extension is not None:
            fname = fname + extension

        return pathjoin(basedir, fname)


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
