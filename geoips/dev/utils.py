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

    General utilities for geoips development and processing

    As utility functions are finalized, they will be moved to
    geoips/stable/utils.py module.
'''

import logging
LOG = logging.getLogger(__name__)


# Miscellaneous ###
def deprecation(message):
    import warnings
    warnings.warn(message, DeprecationWarning, stacklevel=2)
    LOG.warning('DeprecationWarning: %s', message)


def replace_geoips_paths(fname, replace_paths=None, base_paths=None):
    ''' Replace standard environment variables with their non-expanded equivalents.
        Ie, replace
            $HOME/geoproc with $GEOIPS_BASEDIR
            $HOME/geoproc/geoips_outdirs with $GEOIPS_OUTDIRS
        This allows generating output YAML fields / NetCDF attributes that can match between different
        instantiations.

        Note it replaces ALL standard variables that have a corresponding <key>_URL variable.

        Additionally, it replaces variables specified in "replace_paths" list with the
        unexpanded environment variable name.

    Args:
        fname (str) :   Full path to a filename on disk
        replace_paths (list) :  DEFAULT: None -> ['GEOIPS_OUTDIRS', 'GEOIPS_BASEDIR']
                                Explicit list of standard variable names you would like replaced.
        base_paths (list) : DEFAULT: None -> geoips.filenames.base_paths
                            List of PATHS dictionaries in which to find the "replace_paths" variables
    Returns:
        (str) : Path to file on disk, with explicit path replaced with environment variable name and/or
                full URL.
    '''

    # Allow multiple sets of base_path replacements
    from geoips.filenames.base_paths import PATHS as geoips_gpaths
    if base_paths is None:
        base_paths = [geoips_gpaths]

    # Replace with specified file system -> URL mapping
    for gpaths in base_paths:
        for key in gpaths.keys():
            if f'{key}_URL' in gpaths:
                fname = fname.replace(gpaths[key], gpaths[f'{key}_URL'])

    # Replace full paths with environment variables
    if replace_paths is None:
        replace_paths = ['GEOIPS_OUTDIRS', 'GEOIPS_BASEDIR']
    for replace_path in replace_paths:
        for gpaths in base_paths:
            if replace_path in gpaths:
                fname = fname.replace(gpaths[replace_path], f'${replace_path}')	
    return fname


def copy_standard_metadata(orig_xarray, dest_xarray, extra_attrs=None):
    attrs = ['start_datetime', 'end_datetime', 'platform_name', 'source_name', 'minimum_coverage', 'data_provider',
             'granule_minutes', 'original_source_filenames', 'sample_distance_km', 'interpolation_radius_of_influence',
             'area_definition']
    if extra_attrs is not None:
        attrs += extra_attrs

    for attr in attrs:
        if attr in orig_xarray.attrs.keys():
            dest_xarray.attrs[attr] = orig_xarray.attrs[attr]


def get_required_geoips_xarray_attrs():
    required_xarray_attrs = ['source_name', 'platform_name', 'data_provider', 'start_datetime', 'end_datetime']
    return required_xarray_attrs


def output_process_times(process_datetimes, num_jobs=None, job_str='GeoIPS 2'):
    ''' Output process times stored within the process_datetimes dictionary
    Args:
        process_datetimes (dict) : dictionary formatted as follows:
            process_datetimes['overall_start'] - overall start datetime of the entire script
            process_datetimes['overall_end'] - overall end datetime of the entire script
            process_datetimes[process_name]['start'] - start time of an individual process
            process_datetimes[process_name]['end'] - end time of an individual process
    '''

    if 'overall_end' in process_datetimes and 'overall_start' in process_datetimes:
        LOG.info('Total Time %s: %s Num jobs: %s',
                 process_datetimes['overall_end'] - process_datetimes['overall_start'],
                 num_jobs,
                 job_str)
    for process_name in process_datetimes.keys():
        if process_name in ['overall_start', 'overall_end']:
            continue
        if 'end' in process_datetimes[process_name]:
            LOG.info('    SUCCESS Process Time %s: %-20s: %s',
                     job_str,
                     process_name,
                     process_datetimes[process_name]['end'] - process_datetimes[process_name]['start'])
        elif 'fail' in process_datetimes[process_name]:
            LOG.info('    FAILED  Process Time %s: %-20s: %s',
                     job_str,
                     process_name,
                     process_datetimes[process_name]['fail'] - process_datetimes[process_name]['start'])
        else:
            LOG.info('    MISSING Process Time %s: %s', job_str, process_name)
