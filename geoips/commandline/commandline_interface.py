"""Code to implement GeoIPS Command Line Interface (CLI).

Will implement a plethora of commands, but for the meantime, we'll work on
'geoips list' and 'geoips run'
"""
import abc
import argparse
from colorama import Fore, Style
import logging
from importlib import resources
import json
from os.path import dirname
import sys
from tabulate import tabulate
import yaml

from geoips.commandline.log_setup import setup_logging
from geoips.geoips_utils import get_entry_point_group

setup_logging()
LOG = logging.getLogger(__name__)


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
        if parent:
            self.subcommand_parser = parent.subparsers.add_parser(
                self.subcommand_name,
                help=self.cmd_instructions[self.subcommand_name]["help_str"],
                usage=self.cmd_instructions[self.subcommand_name]["usage_str"],
            )
        else:
            self.subcommand_parser = argparse.ArgumentParser()
        self.add_arguments()
        self.subcommand_parser.set_defaults(
            exe_command=getattr(self, self.subcommand_name.replace("-", "_")),
        )
        for subcmd_cls in self.subcommand_classes:
            subcmd_cls(parent=parent)

    @abc.abstractproperty
    def subcommand_name(self):
        pass

    @abc.abstractproperty
    def subcommand_classes(self):
        pass

    @abc.abstractmethod
    def add_arguments(self):
        pass

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
                    "Interface_type",
                    "Family",
                    "Plugin Name",
                    "Relative Path",
                ],
                tablefmt="rounded_grid",
            )
        )


class GeoipsCLI:
    """Top-Level Class for the GeoIPS Commandline Interface (CLI).

    This class includes a list of Sub-Command Classes, which will implement the core
    functionality of the CLI. This includes [GeoipsGet, GeoipsList, GeoipsRun] as of
    right now.
    """
    from geoips.commandline.geoips_get import GeoipsGet
    from geoips.commandline.geoips_list import GeoipsList
    from geoips.commandline.geoips_run import GeoipsRun
    # from geoips.commandline.geoips_validate import GeoipsValidate

    subcommand_classes = [GeoipsGet, GeoipsList, GeoipsRun] #, GeoipsValidate]

    def __init__(self):
        """Initialize the GeoipsCLI and each of it's sub-command classes.

        The CLI contains a single top-level argparse.ArgumentParser() which contains
        subparsers related to each subcommand. This ensures that each command has a
        unique set of arguments stemming from command -> subcommand -> sub-subcommand,
        and so on. For example, the GeoipsList Command Class' arguments are inherited
        by all subcommand class of itself, which carry that trend so on until no more
        subcommand classes remain.
        """
        self.parser = argparse.ArgumentParser()
        self.subparsers = self.parser.add_subparsers(help="sub-parser help")

        for subcmd_cls in self.subcommand_classes:
            subcmd_cls(parent=self)

        self.GEOIPS_ARGS = self.parser.parse_args()

    def execute_command(self):
        """Execute the given command."""
        self.GEOIPS_ARGS.exe_command(self.GEOIPS_ARGS)


def main():
    """Entry point for GeoIPS command line interface (CLI)."""
    geoips_cli = GeoipsCLI()
    geoips_cli.execute_command()


if __name__ == "__main__":
    main()