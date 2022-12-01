# # # Distribution Statement A. Approved for public release. Distribution unlimited.
# # #
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # #
# # # This program is free software:
# # # you can redistribute it and/or modify it under the terms
# # # of the NRLMMD License included with this program.
# # #
# # # If you did not receive the license, see
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/
# # # for more information.
# # #
# # # This program is distributed WITHOUT ANY WARRANTY;
# # # without even the implied warranty of MERCHANTABILITY
# # # or FITNESS FOR A PARTICULAR PURPOSE.
# # # See the included license for more details.

def tc_storm_basedir(basedir, tc_year, tc_basin, tc_stormnum):
    ''' Produce base storm directory for TC web output

    Args:
        basedir (str) :  base directory
        tc_year (int) :  Full 4 digit storm year
        tc_basin (str) :  2 character basin designation
                               SH Southern Hemisphere
                               WP West Pacific
                               EP East Pacific
                               CP Central Pacific
                               IO Indian Ocean
                               AL Atlantic
        tc_stormnum (int) : 2 digit storm number
                               90 through 99 for invests
                               01 through 69 for named storms
    Returns:
        (str) : Path to base storm web directory
    '''
    from os.path import join as pathjoin
    path = pathjoin(basedir,
                    'tc{0:04d}'.format(tc_year),
                    tc_basin,
                    '{0}{1:02d}{2:04d}'.format(tc_basin, tc_stormnum, tc_year))
    return path


def update_extra_field(output_dict, xarray_obj, area_def, product_name,
                       extra_field_delimiter='_',
                       existing_extra_field=None,
                       extra_field_provider=True,
                       extra_field_coverage_func=False,
                       extra_field_resolution=False,
                       include_filename_extra_fields=False,
                       ):

    if extra_field_provider is True:
        from geoips.filenames.base_paths import PATHS as gpaths
        extra_field_provider = gpaths['GEOIPS_COPYRIGHT_ABBREVIATED']

    from geoips.dev.product import get_covg_args_from_product

    if 'source_names' in xarray_obj.attrs:
        for source_name in xarray_obj.source_names:
            try:
                covg_args = get_covg_args_from_product(product_name, source_name,
                                                       output_dict=output_dict,
                                                       covg_args_field_name='fname_covg_args')
            except KeyError:
                continue
    else:
        covg_args = get_covg_args_from_product(product_name, xarray_obj.source_name,
                                               output_dict=output_dict,
                                               covg_args_field_name='fname_covg_args')

    extras = []

    if extra_field_provider:
        extras += [f"{extra_field_provider}"]
    if extra_field_coverage_func and 'radius_km' in covg_args:
        extras += [f"cr{covg_args['radius_km']}"]
    if include_filename_extra_fields\
       and 'filename_extra_fields' in xarray_obj.attrs\
       and xarray_obj.filename_extra_fields:
        for field in xarray_obj.filename_extra_fields:
            extras += [f"{xarray_obj.filename_extra_fields[field]}"]

    # This must go first - but no "res" if no other fields
    if extra_field_resolution:
        resolution = max(area_def.pixel_size_x, area_def.pixel_size_y) / 1000.0
        res_str = '{0:0.1f}'.format(resolution).replace('.', 'p')
        if len(extras) > 0:
            res_str = f"res{res_str}"
        extras = [res_str] + extras

    # This doesn't count towards "other fields" for the res in resolution.
    if existing_extra_field:
        extras += [f'{existing_extra_field}']

    extra = extra_field_delimiter.join(extras)
    return extra
