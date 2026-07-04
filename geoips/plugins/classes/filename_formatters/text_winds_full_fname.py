# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Filename formatter for text windspeed products."""

from geoips.interfaces.class_based.filename_formatters import (
    WindsFilenameFormatterPlugin,
)

import logging

from os.path import join as pathjoin

from geoips.filenames.base_paths import PATHS as gpaths

LOG = logging.getLogger(__name__)


class TextWindsFullFnameFilenameFormatterPlugin(WindsFilenameFormatterPlugin):
    """Text Winds Full Fname Filename formatter plugin class."""

    interface = "filename_formatters"
    family = "xarray_metadata_to_filename"
    name = "text_winds_full_fname"

    def call(
        self,
        xarray_obj,
        extension=".txt",
        basedir=pathjoin(gpaths["ANNOTATED_IMAGERY_PATH"], "text_winds"),
    ):
        """Create a single text winds file for all data in the current xarray.

        This text windspeed filename includes YYYYMMDD.HHMN in the filename
        in order to include only the current datafile in the file.

        See Also
        --------
        geoips.plugins.modules.filename_formatters.text_winds_full_fname.
            assemble_windspeeds_text_full_fname
            Shared utility to create filenames with similar formatting requirements.
        """
        return self.assemble_windspeeds_text_full_fname(
            basedir=basedir,
            source_name=xarray_obj.source_name,
            platform_name=xarray_obj.platform_name,
            data_provider=xarray_obj.data_provider,
            product_datetime=xarray_obj.start_datetime,
            dt_format="%Y%m%d.%H%M",
            extension=extension,
            creation_time=None,
        )


PLUGIN_CLASS = TextWindsFullFnameFilenameFormatterPlugin
