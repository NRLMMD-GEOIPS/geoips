# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Filename formatters interface class."""

from os.path import join as pathjoin

from geoips.interfaces.class_based_plugin import BaseClassPlugin
from geoips.interfaces.base import BaseClassInterface


class BaseFilenameFormatterPlugin(BaseClassPlugin, abstract=True):
    """Base class for GeoIPS filename_formatter plugins."""

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
