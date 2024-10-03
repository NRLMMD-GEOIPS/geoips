# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""General high level utilities for geoips processing."""

import argparse
import inspect
import os
from copy import deepcopy
import re
from shutil import get_terminal_size
import json
from tabulate import tabulate

# import yaml
import logging
from importlib import metadata, resources

from geoips.errors import PluginRegistryError, PluginPackageNotFoundError

LOG = logging.getLogger(__name__)


def remove_unsupported_kwargs(module, requested_kwargs):
    """Remove unsupported keyword arguments."""
    module_args = set(inspect.signature(module).parameters.keys())
    unsupported = list(set(requested_kwargs.keys()).difference(module_args))
    if "kwargs" not in module_args:
        for key in unsupported:
            LOG.warning("REMOVING UNSUPPORTED %s key %s", module, key)
            requested_kwargs.pop(key)
    return requested_kwargs


def split_camel_case(input_string):
    """Use Regular Expression to split a string by camel case.

    Parameters
    ----------
    input_string: str
        - The String to split by camel case

    Returns
    -------
    camel_split: list of str
        - A list of strings, each starting with a capital letter
        - Ex: split_camel_case('BaseTextInterface) --> ['Base', 'Text', 'Interface']
    """
    camel_split = re.findall(r"[A-Z](?:[a-z]+|[A-Z]*(?=[A-Z]|$))", input_string)
    return camel_split


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
    plugin_packages = metadata.entry_points(group="geoips.plugin_packages")

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
    import json

    plugin_packages = metadata.entry_points(group="geoips.plugin_packages")
    yaml_plugins = {}
    for pkg in plugin_packages:
        pkg_plug_path = str(resources.files(pkg.value) / "registered_plugins")
        if not os.path.exists(pkg_plug_path):
            raise PluginRegistryError(
                f"Plugin registry {pkg_plug_path} did not exist, "
                "please run 'create_plugin_registries'"
            )
        # This will include all plugins, including schemas, yaml_based,
        # and module_based plugins.
        registered_plugins = json.load(open(pkg_plug_path, "r"))
        # Only pull the "yaml_based" plugins here.
        try:
            for interface in registered_plugins["yaml_based"]:
                if interface not in yaml_plugins:
                    yaml_plugins[interface] = registered_plugins["yaml_based"][
                        interface
                    ]
                else:
                    merge_nested_dicts(
                        yaml_plugins[interface],
                        registered_plugins["yaml_based"][interface],
                    )
        except TypeError:
            raise PluginRegistryError(f"Failed reading {pkg_plug_path}.")
    return yaml_plugins


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


def replace_geoips_paths_in_list(
    replace_list, replace_paths=None, base_paths=None, curly_braces=False
):
    """Replace geoips paths for every path-based element in a list."""
    newlist = []
    # Go through each element in the list
    for val in replace_list:
        # If this element is a str, and contains "/", it's probably a path,
        # and we can replace the geoips paths.
        if isinstance(val, str) and "/" in val:
            newlist += [replace_geoips_paths(val)]
        # Otherwise, just put the current element back
        else:
            newlist += [val]
    return newlist


def replace_geoips_paths_in_dict(
    replace_dict, replace_paths=None, base_paths=None, curly_braces=False
):
    """Replace geoips paths in every path-based element within a dictionary."""
    dump_dict = replace_dict.copy()
    for key in replace_dict:
        # If this is a string, and it contains "/", replace the geoips paths.
        if isinstance(replace_dict[key], str) and "/" in replace_dict[key]:
            dump_dict[key] = replace_geoips_paths(replace_dict[key])
        # If this is a list, go through each element and replace geoips paths if
        # applicable.
        if isinstance(replace_dict[key], list):
            dump_dict[key] = replace_geoips_paths_in_list(
                replace_dict[key], replace_paths, base_paths, curly_braces
            )
    return dump_dict


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


def merge_nested_dicts(dest, src, in_place=True, replace=False):
    """Perform an in-place merge of src into dest.

    Performs an in-place merge of src into dest while preserving any values that already
    exist in dest.
    """
    if not in_place:
        final_dest = deepcopy(dest)
    else:
        final_dest = dest

    # NOTE: this is a top-level field, where if you set
    # product_spec_override:
    #   replace: true
    # It will automatically replace ALL fields found in
    # the original product spec and also found in the
    # override with what is specified in the override
    # in its entirety, without merging.  This is not
    # terribly useful overall - we probably want this
    # sort of capability in the end, but more flexible
    # and able to be applied to only specific fields,
    # etc.  This is a brute force method to at least
    # allow overriding entire fields.
    if replace:
        for key in final_dest:
            if key in src:
                final_dest[key] = src[key]
        return final_dest

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


def expose_geoips_commands(pkg_name=None, _test_log=None):
    """Expose a list of commands that operate in the GeoIPS environment.

    Where, these commands are defined under 'pyproject.toml:[tool.poetry.scripts]',
    or 'pyproject.toml:[project.entry-points.console_scripts]'

    Parameters
    ----------
    pkg_name: str (default = None)
        - The name of the GeoIPS Plugin Package whose command's will be exposed.
        - If None, assume this was called via the commandline and retrieve package_name
          via that manner. Otherwise use the supplied package_name.
    _test_log: logging.Logger (default = None)
        - If provided, use this logger instead. This is added as an optional argument
          so we can check the output of this command for our Unit Tests.
    """
    pkg_name, log = _get_pkg_name_and_logger(pkg_name, _test_log)
    # Get a list of console_script entrypoints specific to the provided package
    eps = list(
        filter(
            lambda ep: pkg_name in ep.value,
            metadata.entry_points().select(group="console_scripts"),
        )
    )
    log.interactive("-" * len(f"Available {pkg_name.title()} Commands"))
    log.interactive(f"Available {pkg_name.title()} Commands")
    log.interactive("-" * len(f"Available {pkg_name.title()} Commands"))
    if eps:
        table_data = [[ep.name, ep.value] for ep in eps]
        # Log the commands found in a tabular fashion
        log.interactive(
            tabulate(
                table_data,
                headers=["Command Name", "Command Path"],
                tablefmt="rounded_grid",
                maxcolwidths=get_terminal_size().columns // 2,
            )
        )
        # Otherwise let the user know that there were not commands found for this
        # package.
    else:
        log.interactive(f"No '{pkg_name.title()}' Commands were found.")


def _get_pkg_name_and_logger(pkg_name, provided_log):
    """Return the corresponding package name and logger for exposing package commands.

    If pkg_name is None, retrieve pkg_name from the commandline arguments
    (either -p <package_name> or default 'geoips'). If log is None, set log to the LOG
    attribute found in this module.

    If either variable isn't None, use what's provided instead. This is used for
    unit testing primarily.

    Parameters
    ----------
    pkg_name: str
        - The name of the GeoIPS Plugin Package whose command's will be exposed.
        - If None, assume this was called via the commandline and retrieve package_name
          via that manner. Otherwise use the supplied package_name.
        - If supplied, pkg_name must be one of pip installed 'geoips.plugin_packages'.
          ie. 'recenter_tc', 'geoips_clavrx', 'data_fusion', <your_custom_pkg>, ...
    provided_log: logging.Logger
        - If None, retrieve the LOG attribute from this module, otherwise use the
          provided logger so we can check the output of this function for unit tests.

    Returns
    -------
    pkg_name, log: str, logging.Logger
        - The name of the package to retrieve commands from and the logger used to
          output it.
    """
    plugin_packages = [
        str(ep.value) for ep in metadata.entry_points(group="geoips.plugin_packages")
    ]
    if provided_log:
        log = provided_log
    else:
        log = LOG
    if pkg_name is None:
        # This function was called via the command line or None was passed.
        argparser = argparse.ArgumentParser("expose command")
        argparser.add_argument(
            "--package_name",
            "-p",
            type=str.lower,
            default="geoips",
            choices=plugin_packages,
            help="GeoIPS Plugin package to expose.",
        )
        ARGS = argparser.parse_args()
        pkg_name = ARGS.package_name
    else:
        # This function was called via python
        if pkg_name not in plugin_packages:
            raise PluginPackageNotFoundError(
                f"No such package named '{pkg_name}' found. Make sure that package is "
                "installed with a package manager such as pip."
            )
    return pkg_name, log


def is_editable(package_name):
    """Return whether or not 'package_name' has been installed in editable mode.

    Where editable mode is a local package installed via 'pip install -e <path_to_pkg>
    and non-editable mode is a local package installed via 'pip install <pact_to_pkg>.

    If the package under package_name doesn't exist, raise a ValueError reporting that.

    Parameters
    ----------
    package_name: str
        - The name of the pip installed local package. (ie. "geoips", "recenter_tc", ..)

    Returns
    -------
    editable: bool
        - The truth value as to whether or not the package was installed in editable
          mode.
    """
    plugin_package_names = [
        ep.value for ep in metadata.entry_points(group="geoips.plugin_packages")
    ]
    if package_name not in plugin_package_names:
        raise ValueError(
            f"Package '{package_name}' is not an installed package. Please install it "
            "before running this command; ie via 'pip install <path_to_package_name>' "
            "optionally with the '-e' flag. You can also use another package manager."
        )
    dist_info = metadata.distribution(package_name).read_text("direct_url.json")
    # If dist_info is None, package was not installed from source and it was installed
    # from a pre-built wheel. Therefore it is not in editable mode.
    if dist_info:
        # If dist_info is not None, that means we retrieved metadata about the installed
        # package. Check to see if it's in editable mode or not.
        json_dist = json.loads(dist_info)
        if (
            "dir_info" in json_dist.keys()
            and "editable" in json_dist["dir_info"].keys()
            and json_dist["dir_info"]["editable"]
        ):
            # If the 'editable' key exists and is True
            return True
    # Package is installed in non-editable mode
    return False
