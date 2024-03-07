"""Code to implement GeoipsCommand Abstract Base Class for the CLI.

Will implement a plethora of commands, but for the meantime, we'll work on
'geoips get', 'geoips list', 'geoips run', and 'geoips validate'.
"""
import abc
import argparse
from colorama import Fore, Style
from importlib import resources
import json
from os.path import dirname
from tabulate import tabulate
import yaml

from geoips.geoips_utils import get_entry_point_group

class GeoipsCommand(abc.ABC):
    """GeoipsCommand Abstract Base Class.

    This class is a blueprint of what each GeoIPS Sub-Command Classes should implement.
    """

    def __init__(self, parent=None):
        """Initialize GeoipsCommand with a subparser and default to the command func.

        Do this for each GeoipsCLI.geoips_subcommand_classes. This will instantiate
        each subcommand class with a parser and point towards the correct default
        function to call if that subcommand has been called.
        """
        self.nrl_url = "https://github.com/NRLMMD-GEOIPS/"
        if parent:
            if parent.subcommand_name == "cli":
                combined_name = self.subcommand_name
            else:
                combined_name = f"{parent.subcommand_name} {self.subcommand_name}"
            self.subcommand_parser = parent.subparsers.add_parser(
                self.subcommand_name,
                help=self.cmd_instructions[combined_name]["help_str"],
                usage=self.cmd_instructions[combined_name]["usage_str"],
            )
        else:
            self.subcommand_parser = argparse.ArgumentParser()
            combined_name = self.subcommand_name
        self.add_subparsers()
        self.add_arguments()
        self.subcommand_parser.set_defaults(
            exe_command=getattr(self, "__call__"),
        )

    @abc.abstractmethod
    def __call__(self, args):
        """The actual functionaly of the command being called.

        Parameters
        ----------
        args: argparse Namespace()
            - The namespace of the arguments of a specific CLI Command.
        """
        pass

    @property
    @abc.abstractmethod
    def subcommand_name(self):
        """Name of the subcommand_class."""
        pass

    @property
    @abc.abstractmethod
    def subcommand_classes(self):
        """List of subcommand_classes related to the top level command.

        For example, if the class provided was GeoipsList, subcommand_classes would
        be the list of available subcommand_classes that "geoips list" implements.
        """
        pass

    @abc.abstractmethod
    def add_arguments(self):
        """Add arguments related to the sub-command class.

        This is an abstract method because we don't know which arguments need to be
        added for each class at this moment.
        """
        pass

    def add_subparsers(self):
        """Add subparsers for each sub-command class.

        This is done so we can limit the scope of what arguments are accepted for each
        geoips <cmd> sub-command. This is only done for the top-level command, such as
        "list", "run", "get", etc.

        For example, if this were the GeoipsList Command Sub-Class, we would create a
        self.list_subparsers attribute, which we then add individual parsers for each
        sub-command, as in interfaces, plugins, packages, scripts, etc.
        """
        if len(self.subcommand_classes):
            self.subparsers = self.subcommand_parser.add_subparsers(
                help=f"{self.subcommand_name} instructions."
            )
            for subcmd_cls in self.subcommand_classes:
                subcmd_cls(parent=self)

    @property
    def cmd_instructions(self):
        """Dictionary of Instructions for each command, obtained by a yaml file.

        For more information on what's available, see:
            geoips/commandline/ancillary_info/cmd_instructions.yaml
        """
        if not hasattr(self, "_cmd_instructions"):
            cmd_yaml = yaml.safe_load(
                open(
                    str(dirname(__file__)) + "/ancillary_info/cmd_instructions.yaml",
                    "r",
                )
            )
            self._cmd_instructions = {}
            for cmd_entry in cmd_yaml["instructions"]:
                self._cmd_instructions[cmd_entry["cmd_name"]] = {
                    "help_str": cmd_entry["help_str"],
                    "usage_str": cmd_entry["usage_str"],
                    "output_info": cmd_entry["output_info"],
                }
        return self._cmd_instructions

    @property
    def plugin_packages(self):
        """Plugin Packages property of the CLI."""
        if not hasattr(self, "_plugin_packages"):
            self._plugin_packages = [
                ep.value for ep in get_entry_point_group("geoips.plugin_packages")
            ]
        return self._plugin_packages

    @property
    def plugin_package_paths(self):
        """Plugin Package Paths property of the CLI."""
        if not hasattr(self, "_plugin_package_paths"):
            self._plugin_package_paths =  [
                dirname(resources.files(ep.value)) \
                    for ep in get_entry_point_group("geoips.plugin_packages")
            ]
        return self._plugin_package_paths

    def _output_dictionary_highlighted(self, dict_entry):
        """Print to terminal the yaml-dumped dictionary of a certain interface/plugin.

        Color the key, value pairs cyan, yellow to highlight the text in a human
        readable manner. This is done for every `geoips get ...` command.

        Parameters
        ----------
        plugin_entry: dict
            - The dictionary of info for a certain plugin in the plugin registry.
        """
        yaml_text = yaml.dump(dict_entry, default_flow_style=False)
        print()
        for line in yaml_text.split('\n'):
            # Color the keys in cyan and values in yellow
            if ':' in line:
                key, value = line.split(':', 1)
                formatted_line = Fore.CYAN + key + ':' + Style.RESET_ALL
                formatted_line += Fore.YELLOW + value + Style.RESET_ALL
                print(formatted_line)
            else:
                formatted_line = "\t" + Fore.YELLOW + line + Style.RESET_ALL
                print(formatted_line)

    def _get_registry_by_interface_and_package(self, interface, package_name):
        """Retrieve the correct plugin registry given interface and package name.

        Given a GeoIPS Interface and a package name, load in the correct plugin
        registry. This could be the global plugin registry which each interface has
        access to, or it could be the correct interface entry of a certain plugin
        package's "registered_plugins.json", if we are just searching through a
        single package (which occurs when -p <package_name> is given).

        Parameters
        ----------
        interface: geoips.interfaces.<interface_type>
            - The interface we will be parsing and displaying.
        package_name: str
            - The name of the package to retrive the appropriate interfaces from:
              If name is "all", just use the plugin registry that's on all interfaces.

        Returns
        -------
        interface_registry: dict
            - The plugin registry associated with the given interface. If the provided
              interface doesn't exist in a certain package's plugin registry, then None
              is returned instead.
        interface_type: str
            - The type of interface we are dealing with:
              ("module_based", "yaml_based", "text_based")
        """
        if package_name == "all":
            interface_registry = interface.plugin_registry.registered_plugins[
                interface.interface_type
            ][interface.name]
        else:
            interface_registry = json.load(
                open(resources.files(package_name) / "registered_plugins.json", "r")
            )
            if interface.name in interface_registry[interface.interface_type]:
                interface_registry = interface_registry[interface.interface_type][
                    interface.name
                ]
            else:
                return None
        return interface_registry

    def _print_plugins_short_format(self, interface, interface_registry):
        """Print the plugins under a certain interface in alongside minimal info.

        "Short Format" includes these pieces of information:
            [GeoIPS Package, Interface, Plugin Family, Plugin Name, Relpath]

        Parameters
        ----------
        interface: geoips.interfaces.<interface_type>
            - The interface we will be parsing and displaying.
        interface_registry: dict
            - The plugin registry associated with the given interface.
        """
        table_data = []
        for plugin_key in sorted(interface_registry.keys()):
            if interface.name == "products":
                plugin_entry = [
                    "Not Implemented", # Package
                    interface.name, # Interface
                    interface.interface_type, # Interface Type
                    "list", # Family
                    plugin_key, # Plugin Name
                    "Not Implemented", # Relpath
                ]
            else:
                plugin_entry = [
                    interface_registry[plugin_key]["package"],
                    interface.name,
                    interface.interface_type,
                    interface_registry[plugin_key]["family"],
                    plugin_key,
                    interface_registry[plugin_key]["relpath"],
                ]
            table_data.append(plugin_entry)
        print(
            tabulate(
                table_data,
                headers=[
                    "GeoIPS Package",
                    "Interface",
                    "Interface Type",
                    "Family",
                    "Plugin Name",
                    "Relative Path",
                ],
                tablefmt="rounded_grid",
            )
        )