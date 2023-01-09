# # # Distribution Statement A. Approved for public release. Distribution unlimited.
# # #
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # #
# # # This program is free software: you can redistribute it and/or modify it under
# # # the terms of the NRLMMD License included with this program. This program is
# # # distributed WITHOUT ANY WARRANTY; without even the implied warranty of
# # # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the included license
# # # for more details. If you did not receive the license, for more information see:
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/

'''Clean TC filename production'''

from geoips.filenames.base_paths import PATHS as gpaths

filename_type = 'standard'


def tc_clean_fname(area_def, xarray_obj, product_name, coverage, output_type='png', output_type_dir=None,
                   product_dir=None, product_subdir=None, source_dir=None, basedir=gpaths['TCWWW'],
                   output_dict=None):
    ''' Standard type filename module to produce output filenames for "clean" TC products (no gridlines, titles, etc)
    This ensures output ends up in "png_clean" directory, with "-clean" appended to the extra field, to
    avoid conflict with tc_fname based annotated imagery.  Uses "tc_fname" module as a base.

    Args:
        area_def (pyresample AreaDefinition) : Contains metadata regarding sector
        xarray_obj (xarray Dataset) : Contains metadata regarding dataset
        product_name (str) : String product_name specification for use in filename
        coverage (float) : Percent coverage, for use in filename
        output_type (str) : DEFAULT png. Requested output format, ie png, jpg, tif, etc.
        output_type_dir (str) : DEFAULT None. Directory name for given output type (ie png_clean, png, etc)
        product_dir (str) : DEFAULT None. Directory name for given product, defaults to product_name if not specified.
        product_subdir (str) : DEFAULT None. Subdir name for given product, if any.
        source_dir (str) : DEFAULT None. Directory name for given source, xarray_obj.source_name if not specified.
        basedir (str) : DEFAULT $TCWWW. Base directory.
    Returns:
        (str) : Full path to output "clean" filename - with "-clean" appended to extra field,
                and "_clean" appended to output_type_dir.
    '''
    from geoips.interfaces import filename_formatters
    return filename_formatters.get('tc_fname')(area_def, xarray_obj, product_name, coverage, output_type=output_type,
                                     output_type_dir=output_type+'_clean', product_dir=product_dir,
                                     product_subdir=product_subdir, source_dir=source_dir, basedir=basedir,
                                     extra_field='clean', output_dict=output_dict)
