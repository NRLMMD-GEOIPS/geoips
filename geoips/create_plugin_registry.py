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

LOG = logging.getLogger(__name__)


def get_entry_point_group(group):
    """Get entry point group."""
    if sys.version_info[:3] >= (3, 10, 0):
        return metadata.entry_points(group=group)
    else:
        return metadata.entry_points()[group]


def write_registered_plugins(pkg_dir, plugins):
    """Write dictionary of all plugins available from installed GeoIPS packages.

    Parameters
    ----------
    plugins: dict
        A dictionary object of all installed GeoIPS package plugins
    """
    reg_plug_abspath = os.path.join(pkg_dir, "registered_plugins.yaml")
    with open(reg_plug_abspath, "w") as plugin_registry:
        LOG.interactive("Writing %s", reg_plug_abspath)
        yaml.safe_dump(plugins, plugin_registry, default_flow_style=False)


def create_plugin_registry(plugin_packages):
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
    plugins: dict
        A dictionary object of all installed GeoIPS package plugins
    """
    plugins = {
        # "schemas": {},
        "yaml_based": {},
        "module_based": {},
    }
    for pkg in plugin_packages:
        # Track sets of plugins by plugin type
        # (schemas, yaml_based, and module_based)
        package = pkg.value
        LOG.debug("package == " + str(package))
        pkg_plugin_path = resources.files(package) / "plugins"
        pkg_dir = str(resources.files(package))
        yaml_files = pkg_plugin_path.rglob("*.yaml")
        python_files = pkg_plugin_path.rglob("*.py")
        # schema_yaml_path = resources.files(package) / "schema"
        # schema_yamls = schema_yaml_path.rglob("*.yaml")
        plugin_paths = {
            "yamls": yaml_files,
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
        write_registered_plugins(pkg_dir, plugins)


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
    for interface_key in plugin_paths:
        for filepath in plugin_paths[interface_key]:
            filepath = str(filepath)
            # Full path to the plugin file
            abspath = os.path.abspath(filepath)
            # Path relative to the package directory
            relpath = os.path.relpath(filepath, start=package_dir)
            if interface_key == "yamls":  # yaml based plugins
                add_yaml_plugin(
                    filepath, abspath, relpath, package, plugins["yaml_based"]
                )
            # elif interface_key == "schemas":  # schema based yamls
            #     add_schema_plugin(
            #         filepath, abspath, relpath, package, plugins["schemas"]
            #     )
            else:  # module based plugins
                add_module_plugin(abspath, plugins["module_based"])


def add_yaml_plugin(filepath, abspath, relpath, package, plugins):
    """Add the yaml plugin associated with the filepaths and package to plugins.

    Parameters
    ----------
    filepath: str
        The path of the plugin derived from resouces.files(package) / plugin
    abspath: str
        The absolute path to the filepath provided
    relpath: str
        The relative path to the filepath provided
    package: str
        The current GeoIPS package being parsed
    plugins: dict
        A dictionary object of all installed GeoIPS package plugins
    """
    plugin = yaml.safe_load(open(filepath, mode="r"))
    plugin["abspath"] = abspath
    plugin["relpath"] = relpath
    plugin["package"] = package

    interface_name = plugin["interface"]
    interface_module = getattr(geoips.interfaces, f"{interface_name}")

    if interface_name not in plugins.keys():
        plugins[interface_name] = {}

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
                    plugins[interface_name][str(subplg_name)] = {
                        "package": plugin["package"],
                        "relpath": plugin["relpath"],
                        "abspath": plugin["abspath"],
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
        plugins[interface_name][plugin["name"]] = {
            "abspath": abspath,
            "relpath": relpath,
            "package": package,
        }


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


def add_module_plugin(abspath, plugins):
    """Add the yaml plugin associated with the filepaths and package to plugins.

    Parameters
    ----------
    abspath: str
        The absolute path to the module plugin
    plugins: dict
        A dictionary object of all installed GeoIPS package plugins
    """
    if "__init__.py" in abspath:
        return
    module_name = str(abspath).split("/")[-1][:-3]
    spec = util.spec_from_file_location(module_name, abspath)
    try:
        module = util.module_from_spec(spec)
        spec.loader.exec_module(module)
        interface_name = module.interface
        if interface_name not in plugins.keys():
            plugins[interface_name] = {}
        name = module.name
        del module
        plugins[interface_name][name] = {"abspath": abspath}
    except (ImportError, AttributeError) as e:
        LOG.debug(e)
        return


def main():
    """Generate all available plugins from all installed GeoIPS packages.

    After all plugins have been generated, they are written to registered_plugins.yaml
    containing a dictionary of all the registered GeoIPS plugins. Keys in this
    dictionary are the interface names, following by each plugin name.
    """
    LOG = setup_logging(logging_level="INTERACTIVE")
    plugin_packages = get_entry_point_group("geoips.plugin_packages")
    LOG.debug(plugin_packages)
    create_plugin_registry(plugin_packages)
    sys.exit(0)


if __name__ == "__main__":
    main()
