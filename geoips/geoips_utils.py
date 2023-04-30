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

"""General high level utilities for geoips processing."""

import os
import logging
from glob import glob
from importlib import metadata

from geoips.errors import EntryPointError
from geoips.filenames.base_paths import PATHS as gpaths

LOG = logging.getLogger(__name__)

NAMESPACE_PREFIX = "geoips"


def find_config(subpackage_name, config_basename, txt_suffix=".yaml"):
    """Find matching config file within GEOIPS packages.

    Given 'subpackage_name', 'config_basename', and txt_suffix, find matching
    text file within GEOIPS packages.

    Parameters
    ----------
    subpackage_name : str
        subdirectory under GEOIPS package to look for text file
        ie text_fname = geoips/<subpackage_name>/<config_basename><txt_suffix>
    config_basename : str
        text basename to look for,
        ie text_fname = geoips/<subpackage_name>/<config_basename><txt_suffix>
    txt_suffix : str
        suffix to look for on config file, defaults to ".yaml"
        ie text_fname = geoips/<subpackage_name>/<config_basename><txt_suffix>

    Returns
    -------
    text_fname : str
        Full path to text filename
    """
    text_fname = None
    from geoips.filenames.base_paths import PATHS as gpaths

    for package_name in gpaths["GEOIPS_PACKAGES"]:
        fname = os.path.join(
            os.getenv("GEOIPS_PACKAGES_DIR"),
            package_name,
            subpackage_name,
            config_basename + txt_suffix,
        )
        # LOG.info('Trying %s', fname)
        if os.path.exists(fname):
            LOG.info("FOUND %s", fname)
            text_fname = fname
        fname = os.path.join(
            os.getenv("GEOIPS_PACKAGES_DIR"),
            package_name,
            package_name,
            subpackage_name,
            config_basename + txt_suffix,
        )
        # LOG.info('Trying %s', fname)
        if os.path.exists(fname):
            LOG.info("FOUND %s", fname)
            text_fname = fname
    return text_fname


def find_entry_point(namespace, name, default=None):
    """Find object matching 'name' using GEOIPS entry point namespace 'namespace'.

    Automatically add 'geoips' prefix to namespace for disambiguation.

    Parameters
    ----------
    namespace : str
        Entry point namespace (e.g. 'readers')
    name : str
        Entry point name (e.g. 'amsr2_netcdf')
    default : entry point, optional
        Default value if no match is found.  If this is not set (i.e. None),
        then no match will result in an exception
    """
    entry_points = metadata.entry_points()
    ep_namespace = ".".join([NAMESPACE_PREFIX, namespace])
    for ep in entry_points[ep_namespace]:
        if ep.name == name:
            resolved_ep = ep.load()
            break
    else:
        resolved_ep = None
    if resolved_ep is not None:
        return resolved_ep
    else:
        if default is not None:
            return default
        else:
            raise EntryPointError(
                f"Failed to find object matching {name} " "in namespace {ep_namespace}"
            )


def get_all_entry_points(namespace):
    """Return all entry points in GEOIPS entry point namespace 'namespace'.

    Automatically add 'geoips' prefix to namespace for disambiguation.

    Parameters
    ----------
    namespace :str
        Entry point namespace (e.g. 'readers')
    """
    entry_points = metadata.entry_points()
    ep_namespace = ".".join([NAMESPACE_PREFIX, namespace])
    return [ep.load() for ep in entry_points[ep_namespace]]


def list_entry_points(namespace):
    """List names of objects in GEOIPS entry point namespace 'namespace'.

    Automatically add 'geoips' prefix to namespace for disambiguation.

    Parameters
    ----------
    namespace :str
        Entry point namespace (e.g. 'readers')
    """
    entry_points = metadata.entry_points()
    ep_namespace = ".".join([NAMESPACE_PREFIX, namespace])
    return [ep.name for ep in entry_points[ep_namespace]]


def copy_standard_metadata(orig_xarray, dest_xarray, extra_attrs=None, force=True):
    """Copy standard metadata from orig_xarray to dest_xarray.

    Parameters
    ----------
    orig_xarray : xarray.Dataset
        Original xarray to copy attributes from
    dest_xarray : xarray.Dataset
        Destination xarray to copy attributes to
    extra_attrs : list of str, optional
        Additional attributes to copy, beyond the standard metadata, by default None
    force : bool, optional
        If force is True, overwrite existing attributes, by default True

    Returns
    -------
    xarray.Dataset
        dest_xarray with standard metadata copied in place from orig_xarray.
    """
    from geoips.dev.utils import copy_standard_metadata

    return copy_standard_metadata(
        orig_xarray, dest_xarray, extra_attrs=extra_attrs, force=force
    )


def deprecation(message):
    """Print a deprecation warning during runtime."""
    from geoips.dev.utils import deprecation

    return deprecation(message)


def output_process_times(process_datetimes, num_jobs=None):
    """Calculate and print the process times from the process_datetimes dictionary."""
    from geoips.dev.utils import output_process_times

    return output_process_times(process_datetimes, num_jobs=None)
