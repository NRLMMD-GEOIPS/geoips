"""Generates all available plugins from all installed GeoIPS packages.

After all plugins have been generated, they are written to a registered_plugins.yaml
file which contains a dictionary of all the registered GeoIPS plugins.

To use this module, simply call 'python create_plugin_registry.py'.
The main function will do the rest!
"""

import yaml
from importlib import metadata, resources, util
import os
import sys
import logging
from geoips.commandline.log_setup import setup_logging
import geoips.interfaces
from geoips.errors import PluginRegistryError
import json
from argparse import ArgumentParser

LOG = logging.getLogger(__name__)


def remove_registries(plugin_packages):
    """Remove all plugin registries if a PluginRegistryError is raised.

    Parameters
    ----------
    plugin_packages: list EntryPoints
        A list of EntryPoints pointing to each installed
        GeoIPS package --> ie.
        [EntryPoint(name='geoips', value='geoips', group='geoips.plugin_packages'), ...]
    """
    from os import remove
    from os.path import exists

    LOG.interactive(
        "\n\n\n\nERROR: Removing registries due to duplicate plugins. You must fix the "
        "error shown below before GeoIPS can operate correctly.\n"
        "Once fixed, please run 'create_plugin_registries' to set up GeoIPS "
        "appropriately\n\n\n"
    )
    for pkg in plugin_packages:
        yaml_plug_path = str(resources.files(pkg.value) / "registered_plugins.yaml")
        json_plug_path = str(resources.files(pkg.value) / "registered_plugins.json")
        if exists(yaml_plug_path):
            remove(yaml_plug_path)
        if exists(json_plug_path):
            remove(json_plug_path)


def registry_sanity_check(plugin_packages, save_type):
    """Check that each plugin package registry has no duplicate lowest depth entries.

    If it does, raise a PluginRegistryError for that specific package, then remove all
    plugin registries from each package so the user must fix the error before
    continuing. While this doesn't cause a normal error, duplicate plugins will be
    overwritten by same-named plugin found in the last package-entrypoint.

    Parameters
    ----------
    plugin_packages: list EntryPoints
        A list of EntryPoints pointing to each installed
        GeoIPS package --> ie.
        [EntryPoint(name='geoips', value='geoips', group='geoips.plugin_packages'), ...]
    save_type: str
        The file format to save to [json, yaml]
    """
    for comp_idx, comp_pkg in enumerate(plugin_packages):
        # comp_pkg is the package being compared against. This package is compared
        # against every other available GeoIPS package that is installed.
        if save_type == "yaml":
            comp_registry = yaml.safe_load(
                open(resources.files(comp_pkg.value) / "registered_plugins.yaml")
            )
        else:
            comp_registry = json.load(
                open(resources.files(comp_pkg.value) / "registered_plugins.json", "r")
            )
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
            # (schemas, yaml_based, and module_based)
            if save_type == "yaml":
                pkg_registry = yaml.safe_load(
                    open(resources.files(pkg.value) / "registered_plugins.yaml")
                )
            else:
                pkg_registry = json.load(
                    open(resources.files(pkg.value) / "registered_plugins.json", "r")
                )
            for plugin_type in list(pkg_registry.keys()):
                # check the pkg's registry for both yaml-based and module-based plugins
                for interface in comp_registry[plugin_type]:
                    # check each interface of comp_pkg
                    # for each type of plugin (yaml/module)-based
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
                                if (
                                    plugin_type == "module_based"
                                    or "abspath" in pkg_plugin
                                ):
                                    # If the plugin_type is module_based or 'abspath'
                                    # is found in the plugin, raise a
                                    # PluginRegistryError, and remove the registries.
                                    # We do this because either option means you're at
                                    # the lowest depth of the Plugin entry, meaning
                                    # their are two Plugins with Duplicate Names.
                                    remove_registries(plugin_packages)
                                    raise PluginRegistryError(
                                        """Error with packages [{}, {}]:
                                        You can't have two Plugins of the same interface
                                        [{}] with the same name [{}].""".format(
                                            comp_pkg.value,
                                            pkg.value,
                                            interface,
                                            plugin,
                                        )
                                    )
                                # If the statement above is false, that means the plugin
                                # we are dealing with is 'Product'-based. This means
                                # their are subplugins that we need to check against
                                # their defind source names. Grab the comparsion
                                # Product Plugin.
                                comp_plugin = comp_registry[plugin_type][interface][
                                    plugin
                                ]
                                for sub_plg in comp_plugin:
                                    # Loop through each sub-plugin of the comparison
                                    # product plugin.
                                    if sub_plg in pkg_plugin:
                                        # If this sub-plugin is also in the package
                                        # Product plugin, raise a PluginRegistryError
                                        # and remove the registries.
                                        remove_registries(plugin_packages)
                                        raise PluginRegistryError(
                                            """Error with packages [{}, {}]:
                                            You can't have two products of the same
                                            interface [{}] with the same name [{}] found
                                            under source name [{}].""".format(
                                                comp_pkg.value,
                                                pkg.value,
                                                interface,
                                                sub_plg,
                                                plugin,
                                            )
                                        )


def check_plugin_exists(package, plugins, interface_name, plugin_name):
    """Check if plugin already exists, and if it does, raise a PluginRegistryError.

    Parameters
    ----------
    package: str
        The GeoIPS package being tested against
    plugins: dict
        A dictionary object of all installed GeoIPS package plugins
    interface_name: str
        A string representing the GeoIPS interface being checked against
    plugin_name: str
        A string representing the name of the plugin within the GeoIPS interface
    """
    if plugin_name in plugins[interface_name]:
        remove_registries(get_entry_point_group("geoips.plugin_packages"))
        raise PluginRegistryError(
            """Error in package [{}]:
            You can not have two Plugins of the same interface [{}]
            with the same name [{}].""".format(
                package,
                interface_name,
                plugin_name,
            )
        )
    return False


def get_entry_point_group(group):
    """Get entry point group."""
    if sys.version_info[:3] >= (3, 10, 0):
        return metadata.entry_points(group=group)
    else:
        return metadata.entry_points()[group]


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
    """
    if save_type == "yaml":
        reg_plug_abspath = os.path.join(pkg_dir, "registered_plugins.yaml")
        with open(reg_plug_abspath, "w") as plugin_registry:
            LOG.interactive("Writing %s", reg_plug_abspath)
            yaml.safe_dump(plugins, plugin_registry, default_flow_style=False)
    else:
        reg_plug_abspath = os.path.join(pkg_dir, "registered_plugins.json")
        with open(reg_plug_abspath, "w") as plugin_registry:
            LOG.interactive("Writing %s", reg_plug_abspath)
            json.dump(plugins, plugin_registry)


def create_plugin_registries(plugin_packages, save_type):
    """Generate all plugin paths associated with every installed GeoIPS packages.

    These paths include schema plugins, module_based plugins
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
    """
    for pkg in plugin_packages:
        plugins = {
            # "schemas": {},
            "text_based": {},
            "yaml_based": {},
            "module_based": {},
        }
        # Track sets of plugins by plugin type
        # (schemas, yaml_based, and module_based)
        package = pkg.value
        LOG.debug("package == " + str(package))
        pkg_plugin_path = resources.files(package) / "plugins"
        pkg_dir = str(resources.files(package))
        yaml_files = pkg_plugin_path.rglob("*.yaml")
        python_files = pkg_plugin_path.rglob("*.py")
        text_files = pkg_plugin_path.rglob("*.txt")
        # schema_yaml_path = resources.files(package) / "schema"
        # schema_yamls = schema_yaml_path.rglob("*.yaml")
        plugin_paths = {
            "yamls": sorted(yaml_files),
            "text": text_files,
            # "schemas": schema_yamls,
            "pyfiles": python_files,
        }
        parse_plugin_paths(plugin_paths, package, pkg_dir, plugins)
        LOG.debug("Available Plugin Types:\n" + str(plugins.keys()))
        LOG.debug(
            "Available YAML Plugin Interfaces:\n" + str(plugins["yaml_based"].keys())
        )
        LOG.debug(
            "Available Module Plugin Interfaces:\n"
            + str(plugins["module_based"].keys())
        )
        write_registered_plugins(pkg_dir, plugins, save_type)
    registry_sanity_check(plugin_packages, save_type)


def parse_plugin_paths(plugin_paths, package, package_dir, plugins):
    """Parse the plugin_paths provided from the current installed GeoIPS package.

    Then, add them to the plugins dictionary based on the path of the plugin.
    The path contains information as to whether the plugin is a schema, module_based,
    or a normal yaml plugin.

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
    """
    for plugin_type in plugin_paths:
        for filepath in plugin_paths[plugin_type]:
            filepath = str(filepath)
            # Path relative to the package directory
            relpath = os.path.relpath(filepath, start=package_dir)
            if plugin_type == "yamls":  # yaml based plugins
                add_yaml_plugin(filepath, relpath, package, plugins["yaml_based"])
            elif plugin_type == "text":
                add_text_plugin(package, relpath, plugins["text_based"])
            # elif plugin_type == "schemas":  # schema based yamls
            #     add_schema_plugin(
            #         filepath, abspath, relpath, package, plugins["schemas"]
            #     )
            else:  # module based plugins
                add_module_plugin(package, relpath, plugins["module_based"])


def add_yaml_plugin(filepath, relpath, package, plugins):
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
    """
    plugin = yaml.safe_load(open(filepath, mode="r"))
    plugin["relpath"] = relpath
    plugin["package"] = package

    interface_name = plugin["interface"]
    interface_module = getattr(geoips.interfaces, f"{interface_name}")

    if interface_name not in plugins.keys():
        plugins[interface_name] = {}

    check_plugin_exists(package, plugins, interface_name, plugin["name"])

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
            try:
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
                    if str(subplg_name[0]) not in list(plugins[interface_name].keys()):
                        plugins[interface_name][str(subplg_name[0])] = {}
                    pd = None
                    if "product_defaults" in list(yaml_subplg.keys()):
                        pd = yaml_subplg["product_defaults"]
                    family = None
                    if "family" in list(yaml_subplg.keys()):
                        family = yaml_subplg["family"]
                    # since we are dealing with sub-plugins of a product plugin, include
                    # a couple other pieces of information, such as product_defaults
                    # and source_names.
                    if "docstring" not in yaml_subplg:
                        # if the yaml_subplg doesn't include a docstring, grab its
                        # product_defaults docstring
                        docstring = plugins["product_defaults"][
                            yaml_subplg["product_defaults"]
                        ]["docstring"]
                    else:
                        # otherwise use its defined docstring
                        docstring = yaml_subplg["docstring"]
                    plugins[interface_name][str(subplg_name[0])][
                        str(subplg_name[1])
                    ] = {
                        "docstring": docstring,
                        "family": family,
                        "interface": interface_module.name,
                        "package": plugin["package"],
                        "plugin_type": "yaml_based",
                        "product_defaults": pd,
                        "source_names": yaml_subplg["source_names"],
                        "relpath": plugin["relpath"],
                    }
            # If the plugin was not found, issue a warning and continue.
            # Do not fail catastrophically for a bad plugin.
            except KeyError as resp:
                LOG.warning(
                    f"{resp}: from plugin '{plugin.get('name')}',"
                    f"\nin package '{plugin.get('package')}',"
                    f"\nlocated at '{plugin.get('abspath')}' "
                    f"\nMismatched schema and YAML?"
                )
    else:
        # If this is not of family list, just set a single entry for
        # current plugin name.
        # Since this is not a product plugin, we can ensure that these top-level
        # attributes should exist. Don't include product_defaults or source_names in
        # this info, because it doesn't apply to this type of plugin.
        plugins[interface_name][plugin["name"]] = {
            "docstring": plugin["docstring"],
            "family": plugin["family"],
            "interface": plugin["interface"],
            "package": package,
            "plugin_type": "yaml_based",
            "relpath": relpath,
        }


def add_text_plugin(package, relpath, plugins):
    """Add all txt plugins into plugin registries.

    Parameters
    ----------
    package: str
        The current GeoIPS package being parsed
    relpath: str
        The relpath path to the module plugin
    plugins: dict
        A dictionary object of all installed GeoIPS package plugins
    """
    from os.path import basename, splitext

    text_name = splitext(basename(relpath))[0]
    plugins[text_name] = {"package": package, "relpath": relpath}


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


def add_module_plugin(package, relpath, plugins):
    """Add the yaml plugin associated with the filepaths and package to plugins.

    Parameters
    ----------
    package: str
        The current GeoIPS package being parsed
    relpath: str
        The relpath path to the module plugin
    plugins: dict
        A dictionary object of all installed GeoIPS package plugins
    """
    from os.path import basename, splitext

    if "__init__.py" in relpath:
        return
    module_name = splitext(basename(relpath))[0]
    abspath = resources.files(package) / relpath
    spec = util.spec_from_file_location(module_name, abspath)
    try:
        from inspect import signature

        module = util.module_from_spec(spec)
        spec.loader.exec_module(module)
        interface_name = module.interface
        if interface_name not in plugins.keys():
            plugins[interface_name] = {}
        name = module.name
        check_plugin_exists(package, plugins, interface_name, name)
        # Add info shown below obtained from the module plugin. Every module plugin
        # is required to have these entries in the registry to be considered a valid
        # plugin.
        plugins[interface_name][name] = {
            "docstring": module.__doc__,
            "family": module.family,
            "interface": module.interface,
            "package": package,
            "plugin_type": "module_based",
            "signature": str(signature(module.call)),
            "relpath": relpath,
        }
        del module
    except (ImportError, AttributeError) as e:
        LOG.debug(e)
        return


def main():
    """Generate all available plugins from all installed GeoIPS packages.

    After all plugins have been generated, they are written to registered_plugins.yaml
    containing a dictionary of all the registered GeoIPS plugins. Keys in this
    dictionary are the interface names, following by each plugin name.

    Parameters
    ----------
    args: list
        List of strings representing the arguments provided via command line.
    """
    argparser = ArgumentParser(
        prog="create_plugin_registries",
        description="Creates Plugin Registries for available GeoIPS packages.",
    )
    argparser.add_argument(
        "-s", "--save_type", type=str.lower, default="json", choices=["json", "yaml"]
    )
    ARGS = argparser.parse_args()
    save_type = ARGS.save_type

    LOG = setup_logging(logging_level="INTERACTIVE")
    plugin_packages = get_entry_point_group("geoips.plugin_packages")
    LOG.debug(plugin_packages)
    create_plugin_registries(plugin_packages, save_type)
    sys.exit(0)


if __name__ == "__main__":
    main()
