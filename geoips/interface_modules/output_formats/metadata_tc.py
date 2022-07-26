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

import os
import logging

from geoips.filenames.base_paths import PATHS as gpaths
from geoips.dev.utils import replace_geoips_paths
from geoips.sector_utils.yaml_utils import write_yamldict

LOG = logging.getLogger(__name__)

output_type = 'standard_metadata'


def metadata_tc(area_def, xarray_obj, metadata_yaml_filename, product_filename,
                metadata_dir='metadata', basedir=gpaths['TCWWW'], output_dict=None,
                metadata_fname_dict=None, output_fname_dict=None):
    ''' Produce metadata yaml file of sector information associated with the final_product
    Args:
        area_def (AreaDefinition) : Pyresample AreaDefintion object
        final_product (str) : Product that is associated with the passed area_def
        metadata_dir (str) : DEFAULT 'metadata' Subdirectory name for metadata (using non-default allows for
                                                non-operational outputs)

    Returns:
        (str) : Metadata yaml filename, if one was produced.
    '''
    from geoips.sector_utils.utils import is_sector_type
    if not is_sector_type(area_def, 'tc'):
        return None
    # os.path.join does not take a list, so "*" it
    # product_partial_path = product_filename.replace(gpaths['TCWWW'], 'https://www.nrlmry.navy.mil/tcdat')
    product_partial_path = replace_geoips_paths(product_filename)
    # product_partial_path = pathjoin(*final_product.split('/')[-5:-1]+[basename(final_product)])
    return output_tc_metadata_yaml(metadata_yaml_filename, area_def, xarray_obj, product_partial_path, output_dict,
                                   metadata_fname_dict=metadata_fname_dict, output_fname_dict=output_fname_dict)


def update_sector_info_with_coverage(sector_info, product_name, xarray_obj, area_def, output_dict):
    from geoips.dev.product import get_covg_from_product, get_covg_args_from_product

    covg_func_types = ['image_production', 'fname', 'full']

    covg_funcs = {}
    covg_args = {}
    covgs = {}

    default_covg_funcs = get_covg_from_product(product_name,
                                               xarray_obj.source_name,
                                               output_dict=output_dict,
                                               covg_func_field_name='covg_func')

    default_covg_args = get_covg_args_from_product(product_name,
                                                   xarray_obj.source_name,
                                                   output_dict=output_dict,
                                                   covg_args_field_name='covg_args')
    try:
        default_covgs = default_covg_funcs(xarray_obj,
                                           product_name,
                                           area_def,
                                           **covg_args['default'])
    except KeyError:
        LOG.warning('"%s" covg_func not defined, not including in metadata_tc output', 'default')

    for covg_func_type in covg_func_types:
        covg_funcs[covg_func_type] = get_covg_from_product(product_name, xarray_obj.source_name,
                                                           output_dict=output_dict,
                                                           covg_func_field_name=covg_func_type+'_covg_func')
        covg_args[covg_func_type] = get_covg_args_from_product(product_name, xarray_obj.source_name,
                                                               output_dict=output_dict,
                                                               covg_args_field_name=covg_func_type+'_covg_args')
        try:
            covgs[covg_func_type] = covg_funcs[covg_func_type](xarray_obj,
                                                               product_name,
                                                               area_def,
                                                               **covg_args[covg_func_type])
        except KeyError:
            LOG.warning('"%s" covg_func not defined, not including in metadata_tc output', covg_func_type)

    if covgs:
        sector_info['covg_info'] = {}

    for covg_func_type in covgs.keys():
        sector_info['covg_info'][covg_func_type+'_covg_func'] = covg_funcs[covg_func_type].__name__
        sector_info['covg_info'][covg_func_type+'_covg_args'] = covg_args[covg_func_type]
        sector_info['covg_info'][covg_func_type+'_covg'] = covgs[covg_func_type]

    if covgs.keys() and not set(covg_func_types).issubset(set(covgs.keys())):
        sector_info['covg_info']['default_covg_func'] = default_covg_funcs.__name__
        sector_info['covg_info']['default_covg_args'] = default_covg_args
        sector_info['covg_info']['default_covg'] = default_covgs

    return sector_info


def output_tc_metadata_yaml(metadata_fname, area_def, xarray_obj, product_filename=None, output_dict=None,
                            metadata_fname_dict=None, output_fname_dict=None):
    ''' Write out yaml file "metadata_fname" of sector info found in "area_def"

    Args:
        metadata_fname (str) : Path to output metadata_fname
        area_def (AreaDefinition) : Pyresample AreaDefinition of sector information
        xarray_obj (xarray.Dataset) : xarray Dataset object that was used to produce product
        productname (str) : Full path to full product filename that this YAML file refers to
    Returns:
        (str) : Path to metadata filename if successfully produced.
    '''
    from geoips.interface_modules.output_formats.metadata_default import update_sector_info_with_default_metadata
    sector_info = update_sector_info_with_default_metadata(area_def,
                                                           xarray_obj,
                                                           product_filename=product_filename)

    sector_info = update_sector_info_with_coverage(sector_info,
                                                   metadata_fname_dict['product_name'],
                                                   xarray_obj,
                                                   area_def,
                                                   output_dict)

    returns = write_yamldict(sector_info, metadata_fname, force=True)
    if returns:
        LOG.info('METADATASUCCESS Writing %s', metadata_fname)
    return returns

