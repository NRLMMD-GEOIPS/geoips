# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Generates all available plugins from all installed GeoIPS packages.

After all plugins have been generated, they are written to a registered_plugins.json
file which contains a dictionary of all the registered GeoIPS plugins across
all plugin repositories.

Call 'python create_plugin_registry.py' to produce registered_plugins.json for
EVERY currently installed plugin package. A separate registered_plugins.json is
created at the top level package directory for each plugin package.
"""

from argparse import ArgumentParser

# from copy import deepcopy
import logging
from importlib import metadata, resources, util, import_module
from inspect import signature
from os import remove
from os.path import (
    basename,
    dirname,
    split,
    splitext,
    exists,
    join as os_join,
    relpath as os_relpath,
)
import re
import warnings

import json
import yaml

from geoips.errors import PluginRegistryError
import geoips.interfaces

LOG = logging.getLogger(__name__)


def format_docstring(docstring, use_regex=True):
    """Format the provided docstring placement in the plugin registry.

    Found when using the CLI and inspecting the registry, some docstrings are formatted
    in a hard to read manner and look pretty bad. This function will format these
    docstrings to be easily readable, whether obtained via the CLI or manually inspected
    in the plugin registry.

    Parameters
    ----------
    docstring: str
        - The docstring which we are going to format.
    use_regex: bool, optional (default=False)
        - Whether or not we want to apply regex formatting to the docstring. Usually
          recommended as it will replace 'newline' chars but not purposeful
          '.newline' strings.
    """
    if docstring:
        if use_regex:
            # Regex pattern for subbing out "\n" but not ".\n"
            pattern = r"(?<!\.)\n"
            docstring = re.sub(
                pattern,
                " ",
                docstring.strip().replace("\n\n", "\n"),
            )
        else:
            docstring = docstring.strip().replace("\n\n", "\n")
    return docstring


def remove_registries(plugin_packages):
    """Remove all plugin registries if a PluginRegistryError is raised.

    Parameters
    ----------
    plugin_packages: list EntryPoints
        A list of EntryPoints pointing to each installed
        GeoIPS package --> ie.
        [EntryPoint(name='geoips', value='geoips', group='geoips.plugin_packages'), ...]

    Returns
    -------
    None
    """
    # Remove registries is called whenever an improperly formatted plugin or
    # package is encountered.  This is not called until all errors have been
    # collected and reported, to facilitate rapidly identifying and resolving
    # errors.
    LOG.interactive(
        "\n\n\n\nERROR: Removing registries due to improperly formatted plugins.\n"
        "You must fix the error(s) shown below before GeoIPS can operate correctly.\n"
        "Once fixed, please run 'create_plugin_registries' to set up GeoIPS "
        "appropriately\n\n\n"
    )
    # Remove registered_plugins.yaml and registered_plugins.json if they exist
    # for each plugin package.
    for pkg in plugin_packages:
        yaml_plug_path = str(resources.files(pkg.value) / "registered_plugins.yaml")
        json_plug_path = str(resources.files(pkg.value) / "registered_plugins.json")
        if exists(yaml_plug_path):
            remove(yaml_plug_path)
        if exists(json_plug_path):
            remove(json_plug_path)


def registry_sanity_check(plugin_packages, save_type):
    """Check that each plugin package registry has no duplicate lowest depth entries.

    If it does, raise a `PluginRegistryError` for that specific package, then remove all
    plugin registries from each package so the user must fix the error before
    continuing. While this doesn't cause a normal error, duplicate plugins will be
    overwritten by same-named plugin found in the last package-entrypoint.

    Parameters
    ----------
    plugin_packages: list EntryPoints
        A list of EntryPoints pointing to each installed
        GeoIPS package --> ie.
        `[EntryPoint(name='geoips', value='geoips', group='geoips.plugin_packages')]`
    save_type: str
        The file format to save to `[json, yaml]`

    Returns
    -------
    No returns

    Exceptions
    ----------
    PluginRegistryError
        If `error_message` has contents, then raise PluginRegistryError(error_message).
        The `error_message` string will collect and report on all errors within
        this function prior to raising the `PluginRegistryError` to facilitate rapidly
        identifying and resolving errors throughout all plugin packages.
    """
    error_message = ""
    # comp_pkg is the package being compared against. This package is compared
    # against every other available GeoIPS package that is installed.
    for comp_idx, comp_pkg in enumerate(plugin_packages):
        # yaml output is used primarily for testing purposes (since it is more human
        # readable than json), and json output is used for processing. Ensure we
        # can load either option.
        if save_type == "yaml":
            registry_fname = resources.files(comp_pkg.value) / "registered_plugins.yaml"
            with open(registry_fname, "r") as reg_file:
                comp_registry = yaml.safe_load(reg_file)
        else:
            # json.load is much faster than yaml.safe_load
            registry_fname = resources.files(comp_pkg.value) / "registered_plugins.json"
            with open(registry_fname, "r") as reg_file:
                comp_registry = json.load(reg_file)
        for pkg_idx, pkg in enumerate(plugin_packages):
            # pkg is the package being compared against comp_pkg. For example, if
            # comp_pkg was 'geoips', then it would compare against recenter_tc,
            # data_fusion, template_basic_plugin, etc.

            # The if statement below checks the index of pkg_idx and comp_idx.
            # If pkg_idk <= comp_idx, that means it's either the same package as
            # comp_pkg, or that the comparison has already been performed.
            if pkg_idx <= comp_idx:
                continue
            # Track sets of plugins by plugin type
            # (text, yaml_based, and class_based)
            if save_type == "yaml":
                registry_fname = resources.files(pkg.value) / "registered_plugins.yaml"
                with open(registry_fname, "r") as reg_file:
                    pkg_registry = yaml.safe_load(reg_file)
            else:
                registry_fname = resources.files(pkg.value) / "registered_plugins.json"
                with open(registry_fname, "r") as reg_file:
                    pkg_registry = json.load(reg_file)
            for plugin_type in list(pkg_registry.keys()):
                # check the pkg's registry for both yaml-based and class-based plugins
                for interface in comp_registry[plugin_type]:
                    # check each interface of comp_pkg
                    # for each type of plugin (yaml/class)-based
                    if interface in pkg_registry[plugin_type]:
                        # if this interface is also in the pkg_registry, then get the
                        # dictionary of comp_plugins for that interface
                        comp_plugins = comp_registry[plugin_type][interface]
                        for plugin in comp_plugins:
                            # for each plugin in comp_plugins dict
                            if plugin in pkg_registry[plugin_type][interface]:
                                # if this plugin is also in the pkg_registry's
                                # corresponding interface, then retrieve that plugin
                                pkg_plugin = pkg_registry[plugin_type][interface][
                                    plugin
                                ]
                                comp_plugin = comp_registry[plugin_type][interface][
                                    plugin
                                ]
                                if "relpath" in pkg_plugin:
                                    # If 'relpath' is found in the plugin, raise a
                                    # PluginRegistryError, and remove the registries.
                                    # We do this because 'family'  is a top level
                                    # attribute on all plugins, and means you're at
                                    # the lowest depth of the Plugin entry, meaning
                                    # there are two Plugins with Duplicate Names.
                                    error_message += """Error with packages [{}, {}]:
                                        You can't have two Plugins of the same
                                        interface [{}] with the same
                                        plugin name [{}]
                                        pkg relpath: {}
                                        comp relpath: {}""".format(
                                        comp_pkg.value,
                                        pkg.value,
                                        interface,
                                        plugin,
                                        pkg_plugin["relpath"],
                                        comp_plugin["relpath"],
                                    )
                                else:
                                    # If the statement above is false,
                                    # that means the plugin
                                    # we are dealing with is 'Product'-based.
                                    # This means there are subplugins that we
                                    # need to check against their defind
                                    # source names. Grab the comparsion
                                    # Product Plugin.
                                    for sub_plg in comp_plugin:
                                        # Loop through each sub-plugin of the
                                        # comparison product plugin.
                                        if sub_plg in pkg_plugin:
                                            # If this sub-plugin is also in
                                            # the package Product plugin,
                                            # raise a PluginRegistryError
                                            # and remove the registries.
                                            pkg_relpath = "not defined"
                                            if "relpath" in pkg_plugin:
                                                pkg_relpath = pkg_plugin["relpath"]
                                            subplg_relpath = "not defined"
                                            if "relpath" in sub_plg:
                                                subplg_relpath = sub_plg["relpath"]
                                            error_message += """
                                                Error with packages:
                                                [{}, {}]:
                                                You can't have two products of the same
                                                interface [{}] with the same
                                                plugin name [{}] found under
                                                sub_plg name [{}]
                                                relpath: {}
                                                sub_plg relpath: {}\n""".format(
                                                comp_pkg.value,
                                                pkg.value,
                                                interface,
                                                sub_plg,
                                                plugin,
                                                pkg_relpath,
                                                subplg_relpath,
                                            )
    if error_message:
        remove_registries(plugin_packages)
        raise PluginRegistryError(error_message)


def check_plugin_exists(package, plugins, interface_name, plugin_name, relpath):
    """Check if plugin already exists. If it does raise a `PluginRegistryError`.

    Note this only checks for duplicate plugins within a single plugin package.
    The `registry_sanity_check` function is used after all plugins have been
    loaded to identify duplicate plugins across different plugin packages.

    Parameters
    ----------
    package: str
        The GeoIPS package being tested against
    plugins: dict
        A dictionary object of all installed GeoIPS plugins in the current
        plugin package.
    interface_name: str
        A string representing the GeoIPS interface being checked against
    plugin_name: str
        A string representing the name of the plugin within the GeoIPS interface

    Returns
    -------
    error_message : str
        Empty string if no error, appropriate informative error message if
        duplicate plugin found in current plugin package.
    """
    # Check if the passed in plugin_name is already in the current plugin
    # package dictionary for this interface.
    if plugin_name in plugins[interface_name]:
        return f"""\nError in package [{package}]:
            You can not have two Plugins of the same
            interface [{interface_name}] with the same
            name [{plugin_name}] found at
            relpath [{plugins[interface_name][plugin_name]["relpath"]}] and
            relpath [{relpath}]
            """
    return ""


def write_registered_plugins(pkg_dir, plugins, save_type):
    """Write dictionary of all plugins available from installed GeoIPS packages.

    Parameters
    ----------
    pkg_dir: str
        Path in which to write registered_plugins
    plugins: dict
        A dictionary object of all installed GeoIPS package plugins
    save_type: str
        The file format to save to [json, yaml]

    Returns
    -------
    No returns, file written to `pkg_dir`
    """
    if save_type == "yaml":
        reg_plug_abspath = os_join(pkg_dir, "registered_plugins.yaml")
        with open(reg_plug_abspath, "w") as plugin_registry:
            LOG.interactive("Writing %s", reg_plug_abspath)
            yaml.safe_dump(plugins, plugin_registry, default_flow_style=False)
    else:
        reg_plug_abspath = os_join(pkg_dir, "registered_plugins.json")
        with open(reg_plug_abspath, "w") as plugin_registry:
            LOG.interactive("Writing %s", reg_plug_abspath)
            json.dump(plugins, plugin_registry, indent=4)


def create_plugin_registries(plugin_packages, save_type, namespace):
    """Generate all plugin paths associated with every installed GeoIPS packages.

    These paths include text plugins, class_based plugins
    and normal YAML plugins. After these paths are generated, they are sent
    to parse_plugin_paths, which generates and adds the actual plugins to the
    plugins dictionary.

    Parameters
    ----------
    plugin_packages: list EntryPoints
        A list of EntryPoints pointing to each installed
        GeoIPS package --> ie.
        [EntryPoint(name='geoips', value='geoips', group='geoips.plugin_packages'), ...]
    save_type: str
        The file format to save to [json, yaml]
    namespace: str
        Namespace that your plugin packages fall under. The argument parser defaults
        this value to 'geoips.plugin_packages', but a user can create separate
        namespaces if developing interfaces outside of the main GeoIPS package.
    """
    # It appears when there is *.egg-info directory, it picks that package up
    # twice in the list.  If the same package path exists twice, only keep one
    # of them.  This appears to be a bug with Python 3.9 entry points.
    pkg_dirs = []
    unique_package_entry_points = []
    # Note we only use ep.value (resources.files finds the actual plugins),
    # so we do not need to worry about saving the "wrong" package here.
    # We are actually looping through all the files in each package, so
    # we do not have an entry point for every plugin, just a single entry
    # point for each plugin package.
    for ep in plugin_packages:
        pkg_dir = str(resources.files(ep.value))
        if pkg_dir not in pkg_dirs:
            pkg_dirs += [pkg_dir]
            # Grab the unique package entry points.
            unique_package_entry_points += [ep]

    error_message = ""
    # Loop through only the unique package entry points to avoid duplicate
    # plugin errors.
    for pkg in unique_package_entry_points:
        # This is passed by reference and populated with each call to parse
        # plugin packages.
        plugins = {
            "text_based": {},
            "yaml_based": {},
            "class_based": {},
        }
        # Track sets of plugins by plugin type
        # (text_based, yaml_based, and class_based)
        package = pkg.value
        LOG.debug("package == " + str(package))
        # We are specifically looping through all files in the ``plugins``
        # directory within the plugin package. Potentially we may want
        # to update this in the future to actually include package_plugins
        # and package_schema entry points, and point the pyproject.toml
        # package_plugins entry point directly to the appropriate directory
        # that holds all plugins, and the package_schema entry point directly
        # to the directory that holds all scheam, so the subdirectories are
        # not hard coded here in the create_plugin_registries code.
        pkg_plugin_path = resources.files(package) / "plugins"
        pkg_dir = str(resources.files(package))
        # Grab all YAML, Python, and txt files within the plugins directory.
        # YAML schema files may be supported in the future.
        yaml_files = pkg_plugin_path.rglob("*.yaml")
        python_files = pkg_plugin_path.rglob("*.py")
        text_files = pkg_plugin_path.rglob("*.txt")
        # Potentially support installing schema into the geoips name space
        # using entry points as well.  Currently unsupported, but this would
        # allow specifying different YAML plugin schema in different
        # repositories.  Currently all supported YAML plugin formats must be
        # specified in the main geoips repo.
        # schema_yaml_path = resources.files(package) / "schema"
        # schema_yamls = schema_yaml_path.rglob("*.yaml")
        # plugin_paths dictionary contains lists of files for each plugin
        # type (ie, yaml based, text based, and class based plugins, and
        # in the future potentially schema)
        plugin_paths = {
            "yaml": sorted(yaml_files),
            "text": text_files,
            "py_files": python_files,
        }
        # `plugins` is passed by reference and populated with all YAML, text, and
        # python plugins found within the current plugin package `package`.
        # This dictionary is formatted appropriately to be written out to the
        # plugin registry file as either a json or YAML output.
        # If any errors are found, append the error message string to the current
        # error_message.  Do not raise an exception until all plugins have been
        # read in, so we can collect and report on all errors at once.
        error_message += parse_plugin_paths(
            plugin_paths, package, pkg_dir, plugins, namespace
        )
        LOG.debug("Available Plugin Types:\n" + str(plugins.keys()))
        LOG.debug(
            "Available YAML Plugin Interfaces:\n" + str(plugins["yaml_based"].keys())
        )
        LOG.debug(
            "Available Class Plugin Interfaces:\n" + str(plugins["class_based"].keys())
        )
        # Write the current plugin dictionary to the registered plugins file.
        write_registered_plugins(pkg_dir, plugins, save_type)
    # If error_message is not the empty string, that means we had some errors,
    # so handle appropriately.
    if error_message:
        # Remove all registries to prevent running geoips with an incomplete
        # or corrupt set of plugins.  Force user to resolve errors before
        # proceeding.
        remove_registries(metadata.entry_points(group=namespace))
        # Now raise the error, including the error message with output
        # from every failed plugin/file during the attempted registry process.
        raise PluginRegistryError(error_message)
    # Above error only occurs for duplicates within a single registry.
    # registry_sanity_check will check for duplicates across all
    # registries.
    registry_sanity_check(unique_package_entry_points, save_type)


def parse_plugin_paths(plugin_paths, package, package_dir, plugins, namespace):
    """Parse the plugin_paths provided from the current installed GeoIPS package.

    Then, add them to the plugins dictionary based on the path of the plugin.
    The path contains information as to whether the plugin is a class_based, text_based,
    or a yaml_based plugin.

    Parameters
    ----------
    plugin_paths: dict
        A dictionary of filepaths, with keys referring to the type of plugin
    package: str
        The current GeoIPS package being parsed
    package_dir: str
        The path to the current GeoIPS package (for determining relative paths)
    plugins: dict
        A dictionary object of all installed GeoIPS package plugins
    namespace: str
        Namespace that your plugin packages fall under. The argument parser defaults
        this value to 'geoips.plugin_packages', but a user can create separate
        namespaces if developing interfaces outside of the main GeoIPS package.

    Returns
    -------
    error_message: str
        String containing informative error messages from any plugins that
        were improperly formatted.  An exception will be raised at the
        very end if error_message is not the empty string - this allows
        collecting ALL errors throughout the plugin registry process and
        reporting them all at once, to facilitate rapidly identifying and
        resolving errors.
    """
    error_message = ""
    # Loop through each plugin type, ie, text, yaml, class, and later schema.
    for plugin_type in plugin_paths:
        # Loop through each file of the current plugin type.
        for filepath in plugin_paths[plugin_type]:
            filepath = str(filepath)
            # Path relative to the package directory
            relpath = os_relpath(filepath, start=package_dir)
            # plugins is passed by reference, so any new plugins found
            # are added to the plugins dictionary and retained throughout.
            if plugin_type == "yaml":  # yaml based plugins
                error_message += add_yaml_plugin(
                    filepath, relpath, package, plugins["yaml_based"], namespace
                )
            # Ensure we append any errors to the error_message as we go.
            # Exception will not be raised until the very end, when we
            # have collected ALL errors.  This makes it easier to fix
            # all the errors at once.
            elif plugin_type == "text":
                error_message += add_text_plugin(
                    package, relpath, plugins["text_based"]
                )
            # Potentially support schema in the future.
            # elif plugin_type == "schemas":  # schema based yamls
            #     add_schema_plugin(
            #         filepath, abspath, relpath, package, plugins["schemas"]
            #     )
            else:  # Python files; class based plugins
                error_message += add_class_plugin(
                    package, relpath, plugins["class_based"]
                )

    # Ensure we return a string error_message with ALL errors appended.
    # This will be raised at the end if error_message has any contents.
    return error_message


def add_yaml_plugin(filepath, relpath, package, plugins, namespace):
    """Add the yaml plugin associated with the filepaths and package to plugins.

    Parameters
    ----------
    filepath: str
        The path of the plugin derived from resouces.files(package) / plugin
    relpath: str
        The relative path to the filepath provided
    package: str
        The current GeoIPS package being parsed
    plugins: dict
        A dictionary object of all installed GeoIPS package plugins
    namespace: str
        Namespace that your plugin packages fall under. The argument parser defaults
        this value to 'geoips.plugin_packages', but a user can create separate
        namespaces if developing interfaces outside of the main GeoIPS package.

    Returns
    -------
    error_message: str
        String containing informative error messages from any plugins that
        were improperly formatted.  An exception will be raised at the
        very end if error_message is not the empty string - this allows
        collecting ALL errors throughout the plugin registry process and
        reporting them all at once, to facilitate rapidly identifying and
        resolving errors.
    """
    # Since this function always loads all plugins, loading them up front should be
    # fine. It might be good to refactor this at some point. This is a quick fix.
    with open(filepath, "r") as plugin_file:
        new_plugins = list(yaml.load_all(plugin_file, Loader=yaml.SafeLoader))

    for plugin in new_plugins:
        plugin["relpath"] = relpath
        plugin["package"] = package

        try:
            interface_name = plugin["interface"]
        except KeyError:
            raise PluginRegistryError(f"""No 'interface' level in '{filepath}'.
                    Ensure all required metadata is included.""")
        if namespace != "geoips.plugin_packages":
            mod = import_module(package)
            interface_module = getattr(mod.interfaces, f"{interface_name}")
        else:
            interface_module = getattr(geoips.interfaces, f"{interface_name}")

        if interface_name not in plugins.keys():
            plugins[interface_name] = {}

        error_message = ""
        # If the current family is "list", make sure we loop through the list,
        # expanding out each individual product found within the list.
        if plugin["family"] == "list":
            # These are not complete plugins at this stage, only the metadata,
            # so do not validate the plugins here, they will be validated on open.

            # plugin_yaml_to_obj returns the actual plugin object, ie, ProductsPlugin,
            # or SectorsPlugin, etc.
            plg_list = interface_module._plugin_yaml_to_obj(plugin["name"], plugin)

            # plg_list is an e.g. ProductsPlugin object of family list,
            # so within its e.g. plg_list["spec"]["products"] key, we will
            # find a list of all products contained within this single
            # plugin file.
            for yaml_subplg in plg_list["spec"][interface_module.name]:
                # _create_registered_plugin_names will return a list of names
                # found in this single product specification.  Most interfaces
                # this will just return a list of length one, containing
                # [plugin.name], but for products it will return a list of
                # tuples of (source_name, product_name), allowing specifying
                # a list of valid sources within each product spec.
                subplg_names = interface_module._create_registered_plugin_names(
                    yaml_subplg
                )
                # Loop through each of the returned registered plugin names.
                # Give each one its own entry in the plugin registry for easy
                # access.
                for subplg_name in subplg_names:
                    subplg_source = str(subplg_name[0])
                    subplg_product = str(subplg_name[1])
                    if subplg_source not in plugins[interface_name]:
                        plugins[interface_name][subplg_source] = {}
                    # since we are dealing with sub-plugins of a product plugin,
                    # include a couple other pieces of information, such as
                    # product_defaults and source_names.
                    source_names = yaml_subplg["source_names"]
                    pd = None
                    if "product_defaults" in yaml_subplg:
                        pd = yaml_subplg["product_defaults"]
                    family = None
                    if "family" in yaml_subplg:
                        family = yaml_subplg["family"]
                    docstring = None
                    if "docstring" in yaml_subplg:
                        docstring = yaml_subplg["docstring"]
                    # If docstring or family are not specified, and a
                    # product_defaults isn't specified, raise an error
                    # (docstring and family must be defined in a
                    # product_defaults if not defined explicitly).
                    if (not docstring or not family) and not pd:
                        error_message += f"""
                        Error with package '{plugin["package"]}':
                            docstring or family not defined in product,
                            and product_defaults not specified.
                            Must specify docstring and family in either product
                            or product_defaults.
                            interface '{interface_module.name}'
                            plugin name '{plugin["name"]}'
                            pkg relpath: '{plugin["relpath"]}'\n"""
                        continue

                    # I think filling in the nulls should be handled at the CLI
                    # and/or interface level, so leave family/docstring as None
                    # in the registry.
                    # There is no way to guarantee the product_defaults are
                    # available in the same plugin package as the current plugin,
                    # so pulling the family and docstring from the product defaults
                    # when creating the registry will not always work.
                    # If we are concerned about efficiency with opening product and
                    # product_defaults with every plugin access, we could do a
                    # second pass in the plugin registry creation to fill in the
                    # nulls (but we will not worry about that yet)
                    # if not docstring or not family:
                    #     # if the yaml_sub_plg doesn't include a docstring, grab its
                    #     # product_defaults docstring
                    #     if (
                    #         "product_defaults" not in plugins
                    #         or pd not in plugins["product_defaults"]
                    #     ):
                    #         LOG.error(
                    #             f"""Product defaults '{pd}' does not exist.
                    #                   Using 'undefined' docstring.
                    #                   Need to figure out how to pull product defaults
                    #                   from a different plugin package at some point."""  # NOQA
                    #         )
                    #     else:
                    #         if not docstring:
                    #             docstring = plugins["product_defaults"][pd]["docstring"]  # NOQA
                    #         if not family:
                    #             family = plugins["product_defaults"][pd]["family"]
                    plugins[interface_name][subplg_source][subplg_product] = {
                        "docstring": str(format_docstring(docstring)),
                        "family": family,
                        "interface": interface_module.name,
                        "package": plugin["package"],
                        "plugin_type": "yaml_based",
                        "product_defaults": pd,
                        "source_names": source_names,
                        "relpath": plugin["relpath"],
                    }
        else:
            error_message += check_plugin_exists(
                package, plugins, interface_name, plugin["name"], relpath
            )

            # If this is not of family list, just set a single entry for
            # current plugin name.
            # Since this is not a product plugin, we can ensure that these top-level
            # attributes should exist. Don't include product_defaults or source_names in
            # this info, because it doesn't apply to this type of plugin.
            if "docstring" not in plugin:
                error_message += f"""
                Error with package '{plugin["package"]}':
                    docstring or family not defined in product
                    Must specify docstring and family in either product
                    or product_defaults.
                    interface '{plugin["interface"]}'
                    plugin name '{plugin["name"]}'
                    pkg relpath: '{relpath}'\n"""

            else:
                plugins[interface_name][plugin["name"]] = {
                    "docstring": format_docstring(plugin["docstring"]),
                    "family": plugin["family"],
                    "interface": plugin["interface"],
                    "package": package,
                    "plugin_type": "yaml_based",
                    "relpath": relpath,
                }
    return error_message


def add_text_plugin(package, relpath, plugins):
    """Add all text plugins into plugin registries.

    Parameters
    ----------
    package: str
        The current GeoIPS package being parsed
    relpath: str
        The relpath path to the text plugin
    plugins: dict
        A dictionary object of all installed GeoIPS package plugins

    Returns
    -------
    error_message: str
        String containing informative error messages from any plugins that
        were improperly formatted.  An exception will be raised at the
        very end if error_message is not the empty string - this allows
        collecting ALL errors throughout the plugin registry process and
        reporting them all at once, to facilitate rapidly identifying and
        resolving errors.
    """
    # Eventually, we will add interface, family, and name to the text files
    # themselves, in which case we will pull the appropriate information out
    # of the attributes included in the comments at the beginning of the text
    # file. Note I added these comments to the current ascii_palettes, though
    # they are not yet used.

    # For now, use the basename of the filename as the "name"
    text_name = splitext(basename(relpath))[0]

    # For now, use the last directory name as the interface name.
    interface_name = split(dirname(relpath))[-1]
    error_message = ""
    if interface_name not in plugins:
        plugins[interface_name] = {}
    plugins[interface_name][text_name] = {"package": package, "relpath": relpath}
    # For now we have no error messages for text plugins, it will always be
    # an empty string.  But return it anyway.
    return error_message


# def add_schema_plugin(filepath, abspath, relpath, package, plugins):
#     """Add the schema plugin associated with the filepaths and package to plugins.
#
#     Parameters
#     ----------
#     filepath: str
#         The path of the plugin derived from resouces.files(package) / schema
#     abspath: str
#         The absolute path to the filepath provided
#     relpath: str
#         The relative path to the filepath provided
#     package: str
#         The current GeoIPS package being parsed
#     plugins: dict
#         A dictionary object of all installed GeoIPS package plugins
#     """
#     import numpy as np
#
#     split_path = np.array(filepath.split("/"))
#     interface_idx = np.argmax(split_path == "schema") + 1
#     interface_name = split_path[interface_idx]
#     if interface_name not in plugins.keys():
#         plugins[interface_name] = {}
#     plugin = yaml.safe_load(open(filepath, mode="r"))
#     plugin["abspath"] = abspath
#     plugin["relpath"] = relpath
#     plugin["package"] = package
#     plugins[interface_name][plugin["$id"]] = plugin
#     # plugins[interface_name].append(
#     #     {plugin["$id"]: {"$id": plugin["$id"], "abspath": abspath}}
#     # )


def collect_module_plugin_metadata(
    module, module_name, package, relpath, error_message
):
    """Collect metadata for the module-based plugin for the plugin registry.

    Metadata necessary to collect here includes the interface of the plugin, the
    plugin's name, its docstring, and the family it adheres to. Other metadata such as
    relative path and the package it comes from is collected via 'add_class_plugin'.

    NOTE: The 'Returns' section of this docstring is XOR. Either 'metadata' will be
    returned, or 'error_message'. Not both or neither.

    Parameters
    ----------
    module: ModuleType
        - The object of the module which has been loaded in realtime. This should have
          top level attributes such as 'interface', 'name', 'family' and so on.
    module_name: str
        - The name of the .py file.
    package: str
        - The name of the package this plugin comes from
    relpath: str
        - The relative path to the plugin found in 'package'
    error_message: str
        - The current state of errors found during building the registry, stored as a
          string.

    Returns
    -------
    metadata: dict
        - A dictionary of metadata for the provided plugin class to store in the plugin
          registry.
    error_message: str
        - The current state of errors found during building the registry, stored as a
          string.
    """
    # Try to get "interface" variable from the module.  This is required
    # on ALL files within the python module based plugins directory, to
    # ensure create_plugin_registries can explicitly tell whether a file
    # is properly formatted or not.  Files that are not full plugins must
    # be specified with "interface = None" (identifying as a python module
    # that should NOT be included in the python registry), and full GeoIPS
    # plugins must include interface, family, and name variables at the top
    # level.
    try:
        interface_name = module.interface
    except AttributeError:
        error_message += f"""\nError,
            'interface' top level variable missing in
            module '{module_name}' in
            package '{package}'
            at relpath '{relpath}'

            * must specify 'interface' variable at the
            top level of ALL python modules within the
            plugins subdirectory.

            * FOR VALID GEOIPS PLUGINS:
                'interface', 'family', and 'name' must all be specified
                as variables at the top level.

            * FOR HELPER MODULES WITHIN THE plugins SUBDIRECTORY
                'interface = None' must be specified at the top level for modules
                within the plugins subdirectory that are not intended to be
                GeoIPS plugins on their own."""
        return error_message
    # If interface is None, then legitimately skip the module.
    # We want to skip this first, before we test anything else.
    # If it is not a plugin, we don't care if there are other
    # errors in it at this stage (ie, avoid unnecessary unrelated
    # catastrophic failures)
    if not interface_name:
        LOG.interactive(
            f"Skipping module '{module_name}' from '{package}', "
            "interface_name is 'None'"
        )
        return error_message
    # If we get here, it should be a full GeoIPS plugin, so it must include both
    # name and family variables/attributes.
    try:
        name = module.name
        family = module.family
    except AttributeError:
        error_message += f"""\nError, 'family' or 'name' top level variable missing
            in module '{module_name}' in package '{package}'
            at relpath '{relpath}'
            must specify 'interface', 'family', and 'name' variables at the
            top level of ALL module based plugins."""
        return error_message

    metadata = {
        "docstring": format_docstring(module.__doc__),
        "name": name,
        "family": family,
        "interface": interface_name,
        "package": package,
        "plugin_type": "class_based",
        "signature": str(signature(module.call)),
        "relpath": relpath,
        "is_derived_plugin_object": True,
    }

    return metadata


def collect_class_plugin_metadata(plugin_class):
    """Collect metadata linked to the class plugin in 'module' for the plugin registry.

    Metadata necessary to collect here includes the interface of the plugin, the
    plugin's name, its docstring, and the family it adheres to. Other metadata such as
    relative path and the package it comes from is collected via 'add_module_plugin'.

    Parameters
    ----------
    plugin_class: Object, default=None
        - The plugin class from 'module' to collect metadata from. If None, this
          function will attempt to locate the correct plugin class from the provided
          module.

    Returns
    -------
    metadata: dict
        - A dictionary of metadata for the provided plugin class to store in the plugin
          registry.
    """
    # NOTE: Probably should add some attribute checks here as
    # 'collect_module_plugin_metadata' does
    metadata = {
        "docstring": format_docstring(plugin_class.__doc__),
        "name": plugin_class.name,
        "family": plugin_class.family,
        "interface": plugin_class.interface,
        "plugin_type": "class_based",
        "signature": str(signature(plugin_class.call)),
        "is_derived_plugin_object": False,
    }

    return metadata


def add_class_plugin(package, relpath, plugins):
    """Add the class-based plugin associated with the filepaths and package to plugins.

    NOTE: This function will work for 'legacy' module-based plugins that are dynamically
    converted to class-based objects via <interface>.get_plugin and true class-based
    plugins. Stores them all under the 'class_based' portion of the plugin registry and
    denotes whether a plugin is truly class based or not via the metadata variable
    'is_derived_plugin_object'.

    Parameters
    ----------
    package: str
        The current GeoIPS package being parsed
    relpath: str
        The relpath path to the class-based plugin
    plugins: dict
        A dictionary object of all installed GeoIPS package plugins

    Returns
    -------
    error_message: str
        String containing informative error messages from any plugins that
        were improperly formatted. An exception will be raised at the
        very end if error_message is not the empty string - this allows
        collecting ALL errors throughout the plugin registry process and
        reporting them all at once, to facilitate rapidly identifying and
        resolving errors.
    """
    error_message = ""

    if "__init__.py" in relpath:
        # Ignore init files. We should probably ignore other dunder files such as
        # __version.py, etc.
        return error_message

    module_name = splitext(basename(relpath))[0]
    # We need the full path to the module in order
    # for relative imports to work within modules.
    module_path = splitext(relpath.replace("/", "."))[0]
    module_path = f"{package}.{module_path}"
    abspath = resources.files(package) / relpath

    spec = util.spec_from_file_location(module_path, abspath)
    module = util.module_from_spec(spec)
    # Attempting importing module, catch ImportError
    # We have to fix these to be able to import the module to
    # see if 'interface' is defined, in order to see if it
    # is a properly formatted python module.
    try:
        spec.loader.exec_module(module)
    except ImportError as resp:
        LOG.exception(resp)
        error_message += f"""\nError {str(resp)}:
                         Failed importing '{module_name}' in
                         package '{package}'
                         at relpath '{relpath}'\n"""
        return error_message

    # We've encountered a truly 'class-based' plugin. I.e. we don't need to generate
    # the plugin object from the module itself. Collect metadata from this plugin
    # in a different fashion to what we've done previously.

    # Once we've fully implemented class-based plugins and removed support for
    # module-based plugins, we can remove this conditional and only keep the 'if'
    # portion of the if-else statement below. The 'else' part of the conditional handles
    # legacy module based plugins for the time being.
    if "classes" in module_path or hasattr(module, "PLUGIN_CLASS"):
        is_class = True
        try:
            PLUGIN_CLASS = getattr(module, "PLUGIN_CLASS")
        except AttributeError:
            plugin_class_error_message = (
                f"Error: Detected class-based plugin at '{module_path}' but couldn't "
                "locate the associated 'PLUGIN_CLASS' variable defining which class in "
                "that module is the actual plugin class to use. \n Please define that "
                "attribute before continuing. It should be a simple module-level "
                "attribute that references the uninstantiated version of your plugin "
                "class."
            )
            error_message += str(plugin_class_error_message)
            return error_message

        plugin_metadata = collect_class_plugin_metadata(PLUGIN_CLASS)
        interface_name = plugin_metadata["interface"]
        name = plugin_metadata.pop("name")

        plugin_metadata["package"] = package
        plugin_metadata["relpath"] = relpath
    else:
        is_class = False
        # Collect top level metadata from the module plugin
        return_type = collect_module_plugin_metadata(
            module, module_name, package, relpath, error_message
        )
        if isinstance(return_type, str):
            # This conditional checks if the returned object is of a string instance. If
            # it is, that means an error message was added and we should just return it
            return return_type
        else:
            # Otherwise, metadata was returned as expected
            plugin_metadata = return_type
            name = plugin_metadata.pop("name")
            interface_name = plugin_metadata["interface"]

    # If the current interface_name is not in the plugins dictionary yet, add it
    # as an empty dictionary.
    if interface_name not in plugins.keys():
        plugins[interface_name] = {}
    # Check_plugin_exists will return a text error message if there are any errors
    # rather than raising an exception.  This allows collecting all errors as
    # we go, and reporting once at the end with an error message including ALL
    # errors found across all plugins in all plugin packages.  Append the new
    # error message to the error messages that have already been collected.
    error_message += check_plugin_exists(
        package, plugins, interface_name, name, relpath
    )

    # Add the generated metadata to the plugin's entry in the registry
    plugins[interface_name][name] = plugin_metadata

    if interface_name == "readers":
        if not is_class and hasattr(module, "source_names"):
            plugins[interface_name][name]["source_names"] = module.source_names
        elif is_class and hasattr(PLUGIN_CLASS, "source_names"):
            plugins[interface_name][name]["source_names"] = PLUGIN_CLASS.source_names
        else:
            warnings.warn(
                (
                    f"Plugin package '{package}'s reader"
                    f" plugin '{name}' is using a deprecated source_names "
                    "implementation. Please add a module-level 'source_names' "
                    "attribute to this plugin and re-run "
                    "'create_plugin_registries'. This will be fully deprecated "
                    "when GeoIPS v2.0.0 is released."
                ),
                DeprecationWarning,
                stacklevel=2,
            )
            plugins[interface_name][name]["source_names"] = ["Unspecified"]

    del module
    # Return the final error message - an exception will be raised at the very
    # end after collecting and reporting on all errors if there were any errors
    # during plugin registry creation.
    return error_message


def get_parser():
    """Create the ArgumentParser for main."""
    description = (
        "Creates Plugin Registries for all installed GeoIPS packages. "
        "The registries will be written to the root directory of each installed "
        "package. The registries will be named either 'registered_plugins.json' "
        "or 'registered_plugins.yaml' depending on which format is chosen. "
        "For additional information on GeoIPS plugin registries please refer to "
        "the GeoIPS documentation."
    )
    parser = ArgumentParser(
        prog="create_plugin_registries",
        description=description,
    )
    parser.add_argument(
        "-s",
        "--save_type",
        type=str.lower,
        default="json",
        choices=["json", "yaml"],
        help="Format to write registries to. This will also be the file extension.",
    )
    parser.add_argument(
        "-p",
        "--package_name",
        type=str.lower,
        default=None,
        help="Package name to create registries for. If not specified, run on all.",
    )
    parser.add_argument(
        "-n",
        "--namespace",
        type=str,
        default="geoips.plugin_packages",
        help=(
            "Namespace that your plugin packages fall under. Defaults to geoips, but a "
            "user can create separate namespaces if developing interfaces outside of "
            "the main GeoIPS package."
        ),
    )
    return parser
