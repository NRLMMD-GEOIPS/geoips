"""Code to implement GeoipsCommand Abstract Base Class for the CLI.

Will implement a plethora of commands, but for the meantime, we'll work on
'geoips config','geoips get', 'geoips list', 'geoips run', 'geoips test', and
'geoips validate'.
"""

import abc
import argparse
from importlib import resources
import json
from os.path import dirname
from shutil import get_terminal_size

from colorama import Fore, Style
from tabulate import tabulate
import yaml

from geoips.commandline.ancillary_info import cmd_instructions
from geoips.geoips_utils import get_entry_point_group


class PluginPackages:
    """Class to hold the plugin packages and their paths.

    This class is used to hold the plugin packages and their paths, which are used
    throughout the CLI to determine which plugins are available to the user. This
    class is used in the GeoipsCLI class to determine which plugins are available to
    the user.

    Moving this to a class reduced GeoIPS CLI startup time by about 30%.
    """

    def __init__(self):
        """Initialize the PluginPackages class.

        Initialize the plugin packages and their paths. This is done by using the
        get_plugin_packages() and get_plugin_package_paths() functions.
        """
        self.entrypoints = [
            ep.value for ep in get_entry_point_group("geoips.plugin_packages")
        ]
        self.paths = [
            dirname(resources.files(ep.value))
            for ep in get_entry_point_group("geoips.plugin_packages")
        ]


plugin_packages = PluginPackages()


class GeoipsCommand(abc.ABC):
    """Abstract Base Class for top-level GeoIPS Command Classes, such as get or list.

    This class is a blueprint of what each top-level GeoIPS Command Classes should
    implement. Includes shared attributes and an ``add_suparsers`` function which is
    used for initializing sub-command classes of a certain GeoIPS Command.
    """

    def __init__(self, parent=None):
        """Initialize GeoipsCommand with a subparser and default to the command func.

        Do this for each GeoipsCLI.geoips_subcommand_classes. This will instantiate
        each subcommand class with a parser and point towards the correct default
        function to call if that subcommand has been called.

        Parameters
        ----------
        parent: optional - GeoipsCommand Class
            - The parent command class that possibly is initializing it's child.
              Ex. GeoipsList would invoke this init function for each of its subcommand
              classes (GeoipsListPackages, GeoipsListScripts, ...). When it invokes this
              init, it supplies 'self' as an argument to follow the correct logic below.
        """
        self.github_org_url = "https://github.com/NRLMMD-GEOIPS/"
        if parent:
            # Parent Command has been passed. Check if this was the CLI or a top-level
            # command such as List or Get. If it's not cli, set their combined name to
            # '<top-level-command_name> <sub-command-name>', and add a parser for that
            # sub command
            if parent.subcommand_name == "cli":
                combined_name = self.subcommand_name
            else:
                combined_name = f"{parent.subcommand_name}_{self.subcommand_name}"
            if parent.cmd_instructions:
                # this is used for testing purposes to ensure failure for invalid
                # help information. If the parent already has cmd_instructions set,
                # use these instructions so we can test proper functionality of the CLI.
                self.cmd_instructions = parent.cmd_instructions
            else:
                # Otherwise use the default cmd_instructions which are used for normal
                # invocation of the CLI.
                self.cmd_instructions = cmd_instructions
            try:

                # attempt to create a sepate sub-parser for the specific sub-command
                # class being initialized
                # So we can separate the commands arguments in a tree-like structure
                self.subcommand_parser = parent.subparsers.add_parser(
                    self.subcommand_name,
                    help=self.cmd_instructions["instructions"][combined_name][
                        "help_str"
                    ],
                    usage=self.cmd_instructions["instructions"][combined_name][
                        "usage_str"
                    ],
                )
            except KeyError:
                raise KeyError(
                    "Error, the supplied command line instructions are improperly "
                    "formatted. You need an 'instructions' entry that contains a "
                    f"'{combined_name}' key."
                )
        else:
            # otherwise initialize a top-level parser for this command.
            self.subcommand_parser = argparse.ArgumentParser()
            combined_name = self.subcommand_name

        self.add_subparsers()

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
    def plugin_package_names(self):
        """List of names of all installed Geoips Plugin Packages."""
        return plugin_packages.entrypoints

    @property
    def plugin_package_paths(self):
        """List of paths to all installed Geoips Plugin Packages."""
        return plugin_packages.paths


class GeoipsExecutableCommand(GeoipsCommand):
    """Abstract Base Class for executable CLI commands, inheriting from GeoipsCommand.

    This class is a blueprint of what each executable GeoIPS Sub-Command Classes
    can implement.
    """

    def __init__(self, parent=None):
        """Initialize GeoipsExecutableCommand.

        This is a child of GeoipsCommand and will invoke the functionaly of
        GeoipsCommand __init__ func alongside additional logic needed to set up
        executable-based commands. This will instantiate each subcommand class with a
        parser and point towards the correct default function to call if that subcommand
        has been called.

        Parameters
        ----------
        parent: optional - GeoipsCommand Class
            - The parent command class that possibly is initializing it's child.
              Ex. GeoipsList would invoke this init function for each of its subcommand
              classes (GeoipsListPackages, GeoipsListScripts, ...). When it invokes this
              init, it supplies 'self' as an argument to follow the correct logic below.
        """
        super().__init__(parent=parent)
        # Since this class is exectuable (ie. not the cli, top-level list...),
        # add available arguments for that command and set that function to
        # the command's executable function (__call__) if that command is called.
        self.add_arguments()
        self.subcommand_parser.set_defaults(
            exe_command=self.__call__,
        )

    @property
    def terminal_width(self):
        """The Width in ANSI-Characters of the User's Terminal.

        Generate this every time as the screen width may change during usage.
        """
        return get_terminal_size().columns - 1

    @abc.abstractmethod
    def add_arguments(self):
        """Add arguments related to the sub-command class.

        This is an abstract method because we don't know which arguments need to be
        added for each class at this moment.
        """
        pass

    @abc.abstractmethod
    def __call__(self, args):
        """Functionality to execute the command being called.

        Parameters
        ----------
        args: argparse Namespace()
            - The namespace of the arguments of a specific CLI Command.
        """
        pass

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
        for line in yaml_text.split("\n"):
            # Color the keys in cyan and values in yellow
            if ":" in line:
                key, value = line.split(":", 1)
                formatted_line = Fore.CYAN + key + ":" + Style.RESET_ALL
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
            # If there are no plugins of current interface, just return None, do not
            # fail catastrophically. This will fail on "sector_adjusters" interface
            # during "geoips list plugins" if only geoips repo is installed (since there
            # are no "sector_adjuster" plugins in the geoips repo)
            if (
                interface.name
                in interface.plugin_registry.registered_plugins[
                    interface.interface_type
                ]
            ):
                interface_registry = interface.plugin_registry.registered_plugins[
                    interface.interface_type
                ][interface.name]
            else:
                interface_registry = None
        else:
            interface_registry = json.load(
                open(resources.files(package_name) / "registered_plugins.json", "r")
            )
            if interface.name in interface_registry[interface.interface_type]:
                interface_registry = interface_registry[interface.interface_type][
                    interface.name
                ]
            else:
                interface_registry = None
        return interface_registry

    def _print_plugins_short_format(self, interface, interface_registry):
        """Print the plugins under a certain interface alongside ancillary information.

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
                product_dict = interface_registry[plugin_key]
                for subplg_name in sorted(product_dict.keys()):
                    plugin_entry = [
                        product_dict[subplg_name]["package"],  # Package
                        interface.name,  # Interface
                        interface.interface_type,  # Interface Type
                        "N/A",  # Family
                        subplg_name,  # Plugin Name
                        product_dict[subplg_name]["source_names"],  # Source Names
                        product_dict[subplg_name]["relpath"],  # Relpath
                    ]
                    table_data.append(plugin_entry)
            else:
                plugin_entry = [
                    interface_registry[plugin_key]["package"],
                    interface.name,
                    interface.interface_type,
                    interface_registry[plugin_key]["family"],
                    plugin_key,
                    "N/A",
                    interface_registry[plugin_key]["relpath"],
                ]
                table_data.append(plugin_entry)
        headers = [
            "GeoIPS Package",
            "Interface",
            "Interface Type",
            "Family",
            "Plugin Name",
            "Source Names",
            "Relative Path",
        ]
        print(
            tabulate(
                table_data,
                headers=headers,
                tablefmt="rounded_grid",
                maxcolwidths=self.terminal_width // len(headers),
            )
        )
