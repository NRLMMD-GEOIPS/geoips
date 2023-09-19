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
from copy import deepcopy
import sys
import yaml
import logging
from glob import glob
from importlib import metadata, resources

from geoips.errors import EntryPointError, PluginError
from geoips.filenames.base_paths import PATHS as gpaths

LOG = logging.getLogger(__name__)

NAMESPACE_PREFIX = "geoips"


def get_entry_point_group(group):
    """Get entry point group."""
    if sys.version_info[:3] >= (3, 10, 0):
        return metadata.entry_points(group=group)
    else:
        return metadata.entry_points()[group]


def find_ascii_palette(name):
    """Find ASCII palette named "name".

    Search the plugins/txt/ascii_palettes directory for ASCII palettes to use
    as colormaps.
    """
    all_plugins = find_all_txt_plugins("txt/ascii_palettes")

    for plugin in all_plugins:
        if name == os.path.splitext(os.path.basename(plugin))[0]:
            return plugin
    raise ValueError(f"Non-existent txt plugin: {name}")


def find_all_txt_plugins(subdir=""):
    """Find all txt plugins in registered plugin packages.

    Search the ``plugins`` directory of each registered plugin package for files ending
    in ``.txt``. Return list of files
    """
    # Load all entry points for plugin packages
    plugin_packages = get_entry_point_group("geoips.plugin_packages")

    # Loop over the plugin packages and load all of their yaml plugins
    txt_files = []
    for pkg in plugin_packages:
        pkg_plugin_path = resources.files(pkg.value) / "plugins" / subdir
        txt_files += pkg_plugin_path.rglob("*.txt")

    return txt_files


def load_all_yaml_plugins():
    """Find all YAML plugins in registered plugin packages.

    Search the ``plugins`` directory of each registered plugin package for files ending
    in ``.yaml``. Read each plugin file
    """
    # Load all entry points for plugin packages
    plugin_packages = get_entry_point_group("geoips.plugin_packages")

    # Loop over the plugin packages and load all of their yaml plugins
    plugins = {}
    for pkg in plugin_packages:
        pkg_plugin_path = resources.files(pkg.value) / "plugins"
        yaml_files = pkg_plugin_path.rglob("*.yaml")

        # Loop over the yaml files from one package
        for yaml_file in yaml_files:
            # Load
            yaml_plugin = yaml.safe_load(open(yaml_file, "r"))

            # Set some additional information on the YAML plugin
            # The name of the package the plugin comes from
            if not yaml_plugin:
                raise PluginError(
                    f"YAML file is empty, please fill {yaml_file} with the "
                    f"appropriate information."
                )
            yaml_plugin["package"] = pkg.value
            # The relative path to the plugin within the package
            yaml_plugin["relpath"] = str(yaml_file.relative_to(pkg_plugin_path))
            # Absolute path to the plugin
            yaml_plugin["abspath"] = str(yaml_file)

            if "interface" not in yaml_plugin:
                raise PluginError(
                    f"YAML file encountered without 'interface' property: {yaml_file}"
                )
            if yaml_plugin["interface"] not in plugins:
                plugins[yaml_plugin["interface"]] = [yaml_plugin]
            else:
                plugins[yaml_plugin["interface"]].append(yaml_plugin)
    return plugins


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
    ep_namespace = ".".join([NAMESPACE_PREFIX, namespace])
    for ep in get_entry_point_group(ep_namespace):
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
                f"Failed to find object matching {name} in namespace {ep_namespace}"
            )


def get_all_entry_points(namespace):
    """Return all entry points in GEOIPS entry point namespace 'namespace'.

    Automatically add 'geoips' prefix to namespace for disambiguation.

    Parameters
    ----------
    namespace :str
        Entry point namespace (e.g. 'readers')
    """
    ep_namespace = ".".join([NAMESPACE_PREFIX, namespace])
    retlist = []
    # Do not use a list comprehension here so we can raise exceptions
    # containing the actual package that errored.
    try:
        for ep in get_entry_point_group(ep_namespace):
            try:
                retlist += [ep.load()]
            except Exception as resp:
                raise EntryPointError(
                    f"{resp}:"
                    f"\nAn error occurred while loading entry point "
                    f"'{ep.name}={ep.value}' entry point."
                    f"\nTry checking to ensure init file exists in package subdir "
                    f"\n(ALL directories containing python files MUST have init file)"
                ) from resp
    except KeyError:
        retlist = []
    return retlist


def list_entry_points(namespace):
    """List names of objects in GEOIPS entry point namespace 'namespace'.

    Automatically add 'geoips' prefix to namespace for disambiguation.

    Parameters
    ----------
    namespace :str
        Entry point namespace (e.g. 'readers')
    """
    ep_namespace = ".".join([NAMESPACE_PREFIX, namespace])
    return [ep.name for ep in get_entry_point_group(ep_namespace)]


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
    attrs = [
        "start_datetime",
        "end_datetime",
        "platform_name",
        "source_name",
        "minimum_coverage",
        "data_provider",
        "granule_minutes",
        "original_source_filenames",
        "source_file_names",
        "sample_distance_km",
        "interpolation_radius_of_influence",
        "area_definition",
    ]
    if extra_attrs is not None:
        attrs += extra_attrs

    for attr in attrs:
        if force and attr in orig_xarray.attrs.keys():
            dest_xarray.attrs[attr] = orig_xarray.attrs[attr]
        elif (
            not force
            and attr in orig_xarray.attrs.keys()
            and attr not in dest_xarray.attrs.keys()
        ):
            dest_xarray.attrs[attr] = orig_xarray.attrs[attr]


def deprecation(message):
    """Print a deprecation warning during runtime."""
    import warnings

    warnings.warn(message, DeprecationWarning, stacklevel=2)
    LOG.warning("DeprecationWarning: %s", message)


def output_process_times(process_datetimes, num_jobs=None, job_str="GeoIPS 2"):
    """Calculate and print the process times from the process_datetimes dictionary.

    Parameters
    ----------
    process_datetimes : dict
        dictionary formatted as follows:

        * ``process_datetimes['overall_start']`` - overall start datetime of
          the entire script
        * ``process_datetimes['overall_end']`` - overall end datetime of the
          entire script
        * ``process_datetimes[process_name]['start']`` - start time of an
          individual process
        * ``process_datetimes[process_name]['end']`` - end time of an
          individual process
    """
    if "overall_end" in process_datetimes and "overall_start" in process_datetimes:
        LOG.info(
            "Total Time %s: %s Num jobs: %s",
            process_datetimes["overall_end"] - process_datetimes["overall_start"],
            num_jobs,
            job_str,
        )
    for process_name in process_datetimes.keys():
        if process_name in ["overall_start", "overall_end"]:
            continue
        if "end" in process_datetimes[process_name]:
            LOG.info(
                "    SUCCESS Process Time %s: %-20s: %s",
                job_str,
                process_name,
                process_datetimes[process_name]["end"]
                - process_datetimes[process_name]["start"],
            )
        elif "fail" in process_datetimes[process_name]:
            LOG.info(
                "    FAILED  Process Time %s: %-20s: %s",
                job_str,
                process_name,
                process_datetimes[process_name]["fail"]
                - process_datetimes[process_name]["start"],
            )
        else:
            LOG.info("    MISSING Process Time %s: %s", job_str, process_name)


def replace_geoips_paths(
    fname,
    replace_paths=None,
    base_paths=None,
    curly_braces=False,
):
    """Replace standard environment variables with their non-expanded equivalents.

    Ie, replace

        * ``$HOME/geoproc/geoips_packages with $GEOIPS_PACKAGES_DIR``
        * ``$HOME/geoproc/geoips_outdirs with $GEOIPS_OUTDIRS``
        * ``$HOME/geoproc with $GEOIPS_BASEDIR``

    This allows generating output YAML fields / NetCDF attributes that can match
    between different instantiations.

    Parameters
    ----------
    fname : str
        Full path to a filename on disk
    replace_paths : list, default=None
        * Explicit list of standard variable names you would like replaced.
        * If None, replace
          ``['GEOIPS_OUTDIRS', 'GEOIPS_PACKAGES_DIR', 'GEOIPS_TESTDATA_DIR',
          'GEOIPS_DEPENDENCIES_DIR', 'GEOIPS_BASEDIR']``
    base_paths : list, default=None
        * List of PATHS dictionaries in which to find the "replace_paths" variables
        * If None, use geoips.filenames.base_paths
    curly_braces: bool, default=False
        * Specifies whether to include curly braces in the environment variables
          or not.

    Returns
    -------
    fname : str
        Path to file on disk, with explicit path replaced with environment
        variable name and/or full URL.

    Notes
    -----
    Note it replaces ALL standard variables that have a corresponding
    ``<key>_URL`` variable.

    Additionally, it replaces variables specified in "replace_paths" list with
    the unexpanded environment variable name.
    """
    # Allow multiple sets of base_path replacements
    from geoips.filenames.base_paths import PATHS as geoips_gpaths

    if base_paths is None:
        base_paths = [geoips_gpaths]

    # Replace with specified file system -> URL mapping
    for paths in base_paths:
        for key in paths.keys():
            if f"{key}_URL" in paths:
                fname = fname.replace(paths[key], paths[f"{key}_URL"])

    # Replace full paths with environment variables
    if replace_paths is None:
        replace_paths = [
            "GEOIPS_OUTDIRS",
            "GEOIPS_PACKAGES_DIR",
            "GEOIPS_TESTDATA_DIR",
            "GEOIPS_DEPENDENCIES_DIR",
            "GEOIPS_BASEDIR",
        ]
    for replace_path in replace_paths:
        for paths in base_paths:
            if replace_path in paths:
                if curly_braces:
                    fname = fname.replace(paths[replace_path], f"${{{replace_path}}}")
                else:
                    fname = fname.replace(paths[replace_path], f"${replace_path}")
    return fname


def get_required_geoips_xarray_attrs():
    """Interface deprecated v2.0."""
    required_xarray_attrs = [
        "source_name",
        "platform_name",
        "data_provider",
        "start_datetime",
        "end_datetime",
    ]
    return required_xarray_attrs


def list_product_specs_dict_yamls():
    """List all YAML files containing product params in all geoips packages.

    Returns
    -------
    list
        List of all product params dict YAMLs in all geoips packages
    """
    all_files = []
    for package_name in gpaths["GEOIPS_PACKAGES"]:
        all_files += glob(
            gpaths["GEOIPS_PACKAGES_DIR"]
            + "/"
            + package_name
            + "/*/yaml_configs/product_params/*/*.yaml"
        )
        all_files += glob(
            gpaths["GEOIPS_PACKAGES_DIR"]
            + "/"
            + package_name
            + "/yaml_configs/product_params/*/*.yaml"
        )
        all_files += glob(
            gpaths["GEOIPS_PACKAGES_DIR"]
            + "/"
            + package_name
            + "/*/yaml_configs/product_params/*.yaml"
        )
        all_files += glob(
            gpaths["GEOIPS_PACKAGES_DIR"]
            + "/"
            + package_name
            + "/yaml_configs/product_params/*.yaml"
        )
    return [fname for fname in all_files if "__init__" not in fname]


def list_product_source_dict_yamls():
    """List all YAML files containing product source specifications.

    Search in all geoips packages.

    Returns
    -------
    list
        List of all product source dict YAMLs in all geoips packages
    """
    all_files = []
    for package_name in gpaths["GEOIPS_PACKAGES"]:
        all_files += glob(
            gpaths["GEOIPS_PACKAGES_DIR"]
            + "/"
            + package_name
            + "/*/yaml_configs/product_inputs/*.yaml"
        )
        all_files += glob(
            gpaths["GEOIPS_PACKAGES_DIR"]
            + "/"
            + package_name
            + "/yaml_configs/product_inputs/*.yaml"
        )
    return [fname for fname in all_files if "__init__" not in fname]


def merge_nested_dicts(dest, src, in_place=True):
    """Perform an in-place merge of src into dest.

    Performs an in-place merge of src into dest while preserving any values that already
    exist in dest.
    """
    if not in_place:
        final_dest = deepcopy(dest)
    else:
        final_dest = dest
    try:
        final_dest.update(src | final_dest)
    except (AttributeError, TypeError):
        return
    try:
        for key, val in final_dest.items():
            try:
                merge_nested_dicts(final_dest[key], src[key])
            except KeyError:
                pass
    except AttributeError:
        raise
    if not in_place:
        return final_dest
