# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""General high level utilities for geoips processing."""

import argparse
import inspect
import os
from copy import deepcopy
from shutil import get_terminal_size
import json
from pathlib import Path
import logging
from importlib import metadata, resources, import_module

from tabulate import tabulate
import numpy as np

from geoips.errors import PluginRegistryError, PluginPackageNotFoundError
from geoips.filenames.base_paths import PATHS as geoips_paths

LOG = logging.getLogger(__name__)


def get_interface_module(namespace):
    """Retrieve the interface module from a given namespace.

    Since this function uses the first portion of a namespace, I.e.
    (geoips.plugin_packages --> geoips), only interfaces implemented in that exact
    package will be recognized in that namespace. This means that if developers or users
    implement new interfaces in the 'geoips.plugin_packages' namespace, they still won't
    be recognized or available for use in GeoIPS.

    To get new interfaces to work, you must implement them in a separate namespace that
    is named the same as the plugin package that implemented them. I.e.
    (splunk.plugin_packages --> splunk). Any other package that falls under that
    namespace can make use of these interfaces, as well as GeoIPS' interfaces.

    Parameters
    ----------
    namespace: str
        - The namespace containg the requested interface module. I.e.
          'geoips.plugin_packages'.
    """
    package_name = namespace.split(".")[0]
    return import_module(package_name).interfaces


def remove_unsupported_kwargs(module, requested_kwargs):
    """Remove unsupported keyword arguments."""
    module_args = set(inspect.signature(module).parameters.keys())
    unsupported = list(set(requested_kwargs.keys()).difference(module_args))
    if "kwargs" not in module_args:
        for key in unsupported:
            LOG.warning("REMOVING UNSUPPORTED %s key %s", module, key)
            requested_kwargs.pop(key)
    return requested_kwargs


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


def order_paths_from_least_to_most_specific(paths):
    """
    Orders a list of filesystem paths from least to most specific.

    This function takes a list of filesystem paths and returns a new list of paths
    ordered from the least specific (higher-level directories) to the most specific
    (subdirectories and files). It expands environmental variables in paths.

    Parameters
    ----------
    paths : list of str or pathlib.Path
        A list of filesystem paths to be ordered.

    Returns
    -------
    list of pathlib.Path
        A list of filesystem paths ordered from least to most specific.

    Examples
    --------
    >>> paths = [
    ...     '/home/user/docs/',
    ...     '/home/user/images/',
    ...     '/home/user/',
    ...     '/home/user/images/photo.jpg'
    ...     '/home/user/docs/report.txt',
    ... ]
    >>> order_paths_from_least_to_most_specific(paths)
    [PosixPath('/home/user/'),
     PosixPath('/home/user/docs/'),
     PosixPath('/home/user/images/'),
     PosixPath('/home/user/docs/report.txt'),
     PosixPath('/home/user/images/photo.jpg')]

    """
    if not paths:
        return []
    ordered_paths = []
    unordered_paths = []
    paths = [Path(os.path.expandvars(p)) for p in paths]
    for i, path in enumerate(paths):
        other_paths = paths[:i] + paths[i + 1 :]
        if all([path not in other_path.parents for other_path in other_paths]):
            # path not in other paths, least specific already
            ordered_paths.append(path)
        else:
            # path in other path, needs more sorting
            unordered_paths.append(path)
    return ordered_paths + order_paths_from_least_to_most_specific(unordered_paths)


def replace_geoips_paths_in_list(
    replace_list, replace_paths=None, base_paths=None, curly_braces=False
):
    """
    Replace GeoIPS paths with geoips settings in elements of a list.

    This function iterates over each element in the provided `replace_list`,
    attempting to replace GeoIPS paths within each element using the
    `replace_geoips_paths` function. If an element raises a `TypeError`
    when cast to a pathlib path, it is skipped.

    Parameters
    ----------
    replace_list : list
        A list of elements to process. Elements can be of any type, but only those that
        are Path-like will be processed.
    replace_paths : dict, optional
        Passed to replace_geoips_paths
    base_paths : dict, optional
        Passed to replace_geoips_paths
    curly_braces : bool, optional
        Passed to replace_geoips_paths

    Returns
    -------
    list
        A new list containing the elements with GeoIPS paths replaced where possible.
        Elements that could not be processed are included unchanged.

    Examples
    --------
    >>> replace_geoips_paths_in_list(['/home/geoips/data/project',
    ... 'no_replacement_here'])
    ['$GEOIPS_DATA_DIR/project', 'no_replacement_here']

    See Also
    --------
    replace_geoips_paths : Function used to replace GeoIPS paths in individual elements.
    """
    new_list = []
    # Go through each element in the list
    for val in replace_list:
        try:
            new_list.append(
                replace_geoips_paths(
                    val,
                    replace_paths=replace_paths,
                    base_paths=base_paths,
                    curly_braces=curly_braces,
                )
            )
        except TypeError:
            # Otherwise, just put the current element back
            new_list.append(val)
            continue
    return new_list


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
    path,
    replace_paths=None,
    base_paths=None,
    curly_braces=False,
):
    """Replace specified sub-paths in path with related environment variable names.

    This function replaces paths in the provided path with their corresponding
    environment variable names. This is useful for generating output paths
    or metadata that are independent of specific installation directories.

    For example, it can replace:

    - ``'/home/user/geoproc/geoips_packages'`` with ``'$GEOIPS_PACKAGES_DIR'``
    - ``'/home/user/geoproc/geoips_outdirs'`` with ``'$GEOIPS_OUTDIRS'``
    - ``'/home/user/geoproc'`` with ``'$GEOIPS_BASEDIR'``

    Parameters
    ----------
    path : str or pathlib.Path
        The path in which to replace base paths.
    replace_paths : list of str, optional
        A list of environment variable names whose corresponding paths should be
        replaced in `path`.
        If `None`, defaults to:

        ``['$GEOIPS_OUTDIRS', '$GEOIPS_PACKAGES_DIR', '$GEOIPS_TESTDATA_DIR',
        '$GEOIPS_DEPENDENCIES_DIR', '$GEOIPS_BASEDIR']``
    base_paths : dict, optional
        A dictionary mapping environment variable names to their corresponding base
        paths.  If `None`, defaults to `geoips.filenames.base_paths.PATH`.
    curly_braces : bool, default=False
        If `True`, includes curly braces in the environment variables
        (e.g., ``'${GEOIPS_BASEDIR}'``),
        otherwise excludes them (e.g., ``'$GEOIPS_BASEDIR'``).

    Returns
    -------
    str
        The path with specified base paths replaced with environment variable names.

    Notes
    -----
    The function iterates over the provided `replace_paths` in reverse order
    (from most specific to least specific) and replaces the first matching base
    path in the given `path` with the corresponding environment variable name.

    Examples
    --------
    >>> path = '/home/user/geoproc/geoips_packages/module/file.py'
    >>> base_paths = {
    ...     'GEOIPS_PACKAGES_DIR': '/home/user/geoproc/geoips_packages',
    ...     'GEOIPS_BASEDIR': '/home/user/geoproc'
    ... }
    >>> replace_geoips_paths(path, base_paths=base_paths)
    '$GEOIPS_PACKAGES_DIR/module/file.py'
    """
    # Allow multiple sets of base_path replacements

    if base_paths is None:
        base_paths = geoips_paths

    # These are the environment variables that are specified in base_paths.py.
    # Eventually we will want to pull these directly from the environment config,
    # for now explicitly list env vars here.
    if replace_paths is None:
        replace_env_vars = [
            "$TCWWW",
            "$PRIVATEWWW",
            "$PUBLICWWW",
            "$GEOTIFF_IMAGERY_PATH",
            "$ANNOTATED_IMAGERY_PATH",
            "$CLEAN_IMAGERY_PATH",
            "$GEOIPS_OUTDIRS",
            "$GEOIPS_PACKAGES_DIR",
            "$GEOIPS_TESTDATA_DIR",
            "$GEOIPS_DEPENDENCIES_DIR",
            "$GEOIPS_BASEDIR",
        ]

    paths_to_be_replaced = [Path(os.path.expandvars(p)) for p in replace_env_vars]
    ordered_path_envvar_dict = {
        replace_env_vars[paths_to_be_replaced.index(replace_path)]: replace_path
        for replace_path in order_paths_from_least_to_most_specific(
            paths_to_be_replaced
        )
    }

    # Replace with specified file system -> URL mapping
    # for paths in base_paths:
    #    for key in paths.keys():
    #        if f"{key}_URL" in paths:
    #            fname = fname.replace(paths[key], paths[f"{key}_URL"])

    path = Path(os.path.expandvars(path))

    # Replace full paths with environment variables
    for env_var, replace_path in ordered_path_envvar_dict.items():
        if replace_path in path.parents:
            env_var = env_var.replace("$", "")
            return str(path).replace(
                str(replace_path),
                f"${{{env_var}}}" if curly_braces else f"${env_var}",
            )
    return str(path)


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


def get_numpy_seeded_random_generator():
    """
    Get a NumPy random generator seeded with a fixed value.

    Returns
    -------
    numpy.random.Generator
        A NumPy random generator initialized with a fixed seed value of 42.

    Notes
    -----
    This function returns a seeded random generator using NumPy's `default_rng`
    function with a fixed seed of 42. Using a fixed seed ensures that the
    random numbers generated by this generator will be reproducible across different
    runs. 42 was chosen because it is the answer to the universe and all things;
    that is to say: it's selection is inconsequential and any other number
    could have been chosen.

    Examples
    --------
    >>> predictable_random = get_numpy_seeded_random_generator()
    >>> predictable_random.integers(0, 10, size=5)
    array([6, 3, 7, 4, 6])  # Example output, will be the same every time

    """
    return np.random.default_rng(seed=42)
