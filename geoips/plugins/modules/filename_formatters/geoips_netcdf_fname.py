# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Standard GeoIPS NetCDF filename production."""

# Python Standard Libraries
import logging

from geoips.filenames.base_paths import PATHS as gpaths
from os.path import join as pathjoin

LOG = logging.getLogger(__name__)

interface = "filename_formatters"
family = "data"
name = "geoips_netcdf_fname"


def call(
    area_def,
    xarray_obj,
    product_names,
    coverage=None,
    output_type="nc",
    output_type_dir=None,
    product_dir=None,
    product_subdir=None,
    source_dir=None,
    basedir=None,
):
    """Filename formatting for standard GeoIPS-style NetCDF outputs.

    This uses the "assemble_geoips_netcdf_fname" function to appropriately
    assemble the filename from a base directory, product name, source
    name, platform nae, sector name, and product time, to allow reuse
    of this basic filename format from multiple filename formatter
    plugins.
    """
    if basedir is None:
        basedir = gpaths["PRECALCULATED_DATA_PATH"]
    ncdf_fname = assemble_geoips_netcdf_fname(
        basedir=basedir,
        product_name="_".join(product_names),
        source_name=xarray_obj.source_name,
        platform_name=xarray_obj.platform_name,
        sector_name=xarray_obj.area_definition.area_id,
        product_datetime=xarray_obj.start_datetime,
    )

    return ncdf_fname


def assemble_geoips_netcdf_fname(
    basedir,
    product_name,
    source_name=None,
    platform_name=None,
    sector_name=None,
    product_datetime=None,
    set_subpath=None,
    time_format="%H%M%S",
):
    """Produce full output product path from product / sensor specifications.

    netcdf paths are of the format:
        <basedir>/<product_name>/<source_name>/<platform_name>/
          <sector_name>/date{%Y%m%d}
    netcdf filenames are of the format:
        <date{%Y%m%d>.<time{%H%M%S}>.<platform_name>.<product_name>.
          <sector_name>.nc

    Parameters
    ----------
    basedir : str
        Base directory (additional subdirectories assembled below basedir)
    product_name : str
        Name of product, used in path and filename
    source_name : str
        Name of data source (sensor), used in path and filename
    platform_name : str
        Name of platform (satellite), used in path and filename
    coverage : float
        Image coverage, float between 0.0 and 100.0, used in filename
    product_datetime : datetime
        Datetime object - start time of data used to generate product, used
        in filename
    """
    if set_subpath:
        path = pathjoin(basedir, set_subpath)
    else:
        path = basedir
        if product_name is not None:
            path = pathjoin(path, product_name)
        if source_name is not None:
            path = pathjoin(path, source_name)
        if platform_name is not None:
            path = pathjoin(path, platform_name)
        if sector_name is not None:
            path = pathjoin(path, sector_name)
        if product_datetime is not None:
            path = pathjoin(path, product_datetime.strftime("%Y%m%d"))
    fname = ""
    path_parts = []
    if product_datetime is not None:
        path_parts.extend(
            [
                product_datetime.strftime("%Y%m%d"),
                product_datetime.strftime(time_format),
            ]
        )
    if platform_name is not None:
        path_parts.extend([platform_name])
    if product_name is not None:
        path_parts.extend([product_name])
    if sector_name is not None:
        path_parts.extend([sector_name])
    fname = ".".join(path_parts + ["nc"])

    return pathjoin(path, fname)
