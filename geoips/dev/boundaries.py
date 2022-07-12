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

''' Interface Under Development.  Please provide feedback to geoips@nrlmry.navy.mil

    Wrapper functions for geoips boundaries plotting parameter specifications

    Once all related wrapper functions are finalized,
    this module will be moved to the geoips/stable sub-package.
'''

import logging
LOG = logging.getLogger(__name__)

from geoips.geoips_utils import find_config


### Gridline parameter dictionaries ###
def is_valid_boundaries(boundaries_name):
    ''' Interface Under Development, please provide feedback to geoips@nrlmry.navy.mil

        Check that requested boundaries parameter dictionary is properly formatted.

        The dictionary of boundaries parameters determines how the boundaries appear on the output
        cartopy imagery.

        Dictionary of boundaries parameters currently specified by:
            yaml_configs.plotting_params.boundaries.<boundaries_name>

    Args:
        boundaries_name (str) : Name of requested boundaries parameter set (ie, 'tc_pmw', 'tc_visir', etc)

    Returns:
        (bool) : True if 'boundaries_name' is a properly formatted dictionary of boundaries parameters.
                 False if boundaries parameter dictionary:
                        does not contain supported 'boundaries_dict_type', 
                        does not contain all 'required' fields,
                        contains non-supported 'optional' fields 

                 Gridline dictionary types currently one of:

                        'standard' : Include coastlines, countries, states, rivers info.
                               dictionary fields: {'boundaries_dict_type': 'standard',
                                                   'request_coastlines': <bool>,
                                                   'request_countries': <bool>,
                                                   'request_states': <bool>,
                                                   'request_rivers': <bool>,
                                                   'coastlines_linewidth': <float>,
                                                   'countries_linewidth': <float>,
                                                   'states_linewidth': <float>,
                                                   'rivers_linewidth': <float>,
                                                   'coastlines_color': <str>,
                                                   'countries_color': <str>,
                                                   'states_color': <str>,
                                                   'rivers_color': <str>}
                                     
    '''

    required_keys = {'standard': ['boundaries_dict_type',
                                  'request_coastlines',
                                  'request_countries',
                                  'request_states',
                                  'request_rivers',
                                  'coastlines_linewidth',
                                  'countries_linewidth',
                                  'states_linewidth',
                                  'rivers_linewidth',
                                  'coastlines_color',
                                  'countries_color',
                                  'states_color',
                                  'rivers_color']}

    optional_keys = {'standard': []}

    field_types = {'standard': {'boundaries_dict_type': str,
                                'request_coastlines': bool,
                                'request_countries': bool,
                                'request_states': bool,
                                'request_rivers': bool,
                                'coastlines_linewidth': float,
                                'countries_linewidth': float,
                                'states_linewidth': float,
                                'rivers_linewidth': float,
                                'coastlines_color': str,
                                'countries_color': str,
                                'states_color': str,
                                'rivers_color': str}}

    boundaries_dict = get_boundaries(boundaries_name)
    # if boundaries_dict is None:
    #     LOG.error("INVALID PRODUCT '%s': boundaries parameter dictionary did not exist",
    #               boundaries_name)
    #     return False

    if 'boundaries_dict_type' not in boundaries_dict:
        LOG.error(f'''INVALID GRIDLINE '{boundaries_name}':
                  'boundaries_dict_type' must be defined within boundaries parameter dictionary''')
        return False
    if boundaries_dict['boundaries_dict_type'] not in required_keys.keys():
        LOG.error(f'''INVALID GRIDLINE '{boundaries_name}':
                  'boundaries_dict_type' in boundaries parameter dictionary must be one of '{list(required_keys.keys())}' ''')
        return False

    boundaries_dict_type = boundaries_dict['boundaries_dict_type']

    # If we don't have all of the required keys, return False
    if not set(required_keys[boundaries_dict_type]).issubset(set(boundaries_dict)):
        LOG.error(f'''INVALID GRIDLINE "{boundaries_name}": boundaries parameter dictionary must contain the following fields:
                  "{list(required_keys.keys())}" ''')
        return False

    # If we have non-allowed keys, return False
    if not set(boundaries_dict).issubset(required_keys[boundaries_dict_type]+optional_keys[boundaries_dict_type]):
        LOG.error(f'''INVALID GRIDLINE "{boundaries_name}": Unknown fields in boundaries parameter dictionary:
                  "{set(boundaries_dict).difference(required_keys[boundaries_dict_type]+optional_keys[boundaries_dict_type])}"''')
        return False

    for field_name in boundaries_dict:
        if not isinstance(boundaries_dict[field_name], field_types[boundaries_dict_type][field_name]):
            try:
                test = field_types[boundaries_dict_type][field_name](boundaries_dict[field_name])
            except Exception:
                LOG.error(f'''INVALID GRIDLINE {boundaries_name}: boundaries field '{field_name}' must be of type "{field_types[boundaries_dict_type][field_name]}"''')
                return False

    # If we get here, then the boundaries parameter dictionary format is valid.
    return True


def get_boundaries(boundaries_name):
    ''' Interface Under Development, please provide feedback to geoips@nrlmry.navy.mil

    Get dictionary of requested boundaries parameters.

    See: geoips.dev.boundaries.is_valid_boundaries for full list of supported boundaries dictionary formats

    Args:
        boundaries_name (str) : Name of requested boundaries (ie, 'tc_pmw', 'visir_pmw', etc)

    Returns:
        (dict) : Dictionary of desired boundaries specifications
    '''
    if boundaries_name is None:
        return None
    boundaries_fname = find_config(subpackage_name='yaml_configs/plotting_params/boundaries',
                                config_basename=boundaries_name)
    import yaml
    with open(boundaries_fname, 'r') as fobj:
        boundaries_dict = yaml.safe_load(fobj)
    if boundaries_name not in boundaries_dict:
        raise ValueError(f'boundaries file {boundaries_fname} must contain boundaries name {boundaries_name} as key')
    return boundaries_dict[boundaries_name]


def get_boundaries_type(boundaries_name):
    ''' Interface Under Development, please provide feedback to geoips@nrlmry.navy.mil

    Retrieve boundaries_dict_type of the requested boundaries, found in:
           geoips.dev.boundaries.get_boundaries(boundaries_name)['boundaries_dict_type']

    See: geoips.dev.boundaries.is_valid_boundaries for full list of supported boundaries dict types.

    Args:
        boundaries_name (str) : Name of requested boundaries (ie, 'tc_pmw', 'visir_pmw', etc)

    Returns:
        (str) : boundaries dict type, found in
                geoips.dev.boundaries.get_boundaries(boundaries_name)['boundaries_dict_type']
    '''
    boundaries_dict = get_boundaries(boundaries_name)
    return boundaries_dict['boundaries_dict_type']


def list_boundaries_by_type():
    ''' Interface Under Development, please provide feedback to geoips@nrlmry.navy.mil

    List all available boundaries settings within the current GeoIPS instantiation, on a per-boundaries_dict_type basis.

    boundaries dict "type" determines exact required format of the boundaries parameter dictionary.

    See geoips.dev.boundaries.is_valid_boundaries? for a list of available boundaries types and associated dictionary formats.
    See geoips.dev.boundaries.get_boundaries(boundaries_name) to retrieve the boundaries parameter dictionary
                                                            for a given boundaries

    Returns:
        (dict) : Dictionary with all boundaries dict types as keys, and lists of associated boundaries names (str) as values.

    '''
    from os.path import basename, splitext
    from geoips.geoips_utils import list_boundaries_params_dict_yamls
    all_files = list_boundaries_params_dict_yamls()
    all_boundaries = {}
    for fname in all_files:
        boundaries_name = splitext(basename(fname))[0]
        if not is_valid_boundaries(boundaries_name):
            continue
        boundaries_dict_type = get_boundaries_type(boundaries_name)
        if boundaries_dict_type not in all_boundaries:
            all_boundaries[boundaries_dict_type] = [boundaries_name]
        else:
            if boundaries_name not in all_boundaries[boundaries_dict_type]:
                all_boundaries[boundaries_dict_type] += [boundaries_name]

    return all_boundaries


def test_boundaries_interface():
    ''' Finds and opens every boundaries params dict available within the current geoips instantiation

    See geoips.dev.boundaries.is_valid_boundaries? for a list of available boundaries params dict types and associated call signatures / return values.
    See geoips.dev.boundaries.get_boundaries(boundaries_params_dict_name) to retrieve the requested boundaries params dict

    Returns:
        (list) : List of all successfully opened geoips boundaries params dicts
    '''
    curr_names = list_boundaries_by_type()
    out_dict = {'by_type': curr_names, 'validity_check': {}, 'dict_type': {}, 'dict': {}}
    for curr_type in curr_names:
        for curr_name in curr_names[curr_type]:
            out_dict['validity_check'][curr_name] = is_valid_boundaries(curr_name)
            out_dict['dict'][curr_name] = get_boundaries(curr_name)
            out_dict['dict_type'][curr_name] = get_boundaries_type(curr_name)
    return out_dict 
