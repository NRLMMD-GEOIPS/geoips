# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Clean TC filename production (no backgrounds or overlays)."""

from geoips.filenames.base_paths import PATHS as gpaths

interface = "filename_formatters"
family = "standard"
name = "tc_clean_fname"


def call(
    area_def,
    xarray_obj,
    product_name,
    coverage=None,
    output_type="png",
    output_type_dir=None,
    product_dir=None,
    product_subdir=None,
    source_dir=None,
    basedir=gpaths["TCWWW"],
    output_dict=None,
):
    """Clean TC product filename formatter (no gridlines, titles, etc).

    This ensures output ends up in "png_clean" directory, with "-clean"
    appended to the extra field, to avoid conflict with tc_fname based
    annotated imagery.  Uses "tc_fname" module as a base.

    Parameters
    ----------
    area_def : pyresample AreaDefinition
        Contains metadata regarding sector
    xarray_obj : xarray Dataset
        Contains metadata regarding dataset
    product_name : str
        String product_name specification for use in filename
    coverage : float
        Percent coverage, for use in filename
    output_type : str, optional
        Requested output format, ie png, jpg, tif, etc, defaults to None.
    output_type_dir : str, optional
        Directory name for given output type (ie png_clean, png, etc), defaults
        to None.
    product_dir : str, optional
        Directory name for given product, defaults to None.
    product_subdir : str, optional
        Subdir name for given product, if any, defaults to None.
    source_dir : str, optional
        Directory name for given source, defaults to None.
    basedir : str, optional
        Base directory, defaults to $TCWWW.

    Returns
    -------
    str
        Full path to output "clean" filename - with "-clean" appended to
        extra field, and "_clean" appended to output_type_dir.
    """
    from geoips.interfaces import filename_formatters

    return filename_formatters.get_plugin("tc_fname")(
        area_def,
        xarray_obj,
        product_name,
        coverage,
        output_type=output_type,
        output_type_dir=output_type + "_clean",
        product_dir=product_dir,
        product_subdir=product_subdir,
        source_dir=source_dir,
        basedir=basedir,
        extra_field="clean",
        output_dict=output_dict,
    )
