# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Code to implement GeoipsCommand Abstract Base Class for the CLI.

Will implement a plethora of commands, but for the meantime, we'll work on
'geoips config','geoips get', 'geoips list', 'geoips run', 'geoips test', and
'geoips validate'.
"""

import abc
import argparse
from importlib import metadata, resources
import json
from os.path import dirname
from shutil import get_terminal_size

from colorama import Fore, Style
from tabulate import tabulate
import yaml

from geoips.commandline.cmd_instructions import cmd_instructions, alias_mapping


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
            ep.value
            for ep in sorted(metadata.entry_points(group="geoips.plugin_packages"))
        ]
        self.paths = [
            dirname(resources.files(ep.value))
            for ep in sorted(metadata.entry_points(group="geoips.plugin_packages"))
        ]


plugin_packages = PluginPackages()


class GeoipsCommand(abc.ABC):
    """Abstract Base Class for top-level GeoIPS Command Classes, such as get or list.

    This class is a blueprint of what each top-level GeoIPS Command Classes should
    implement. Includes shared attributes and an ``add_suparsers`` function which is
    used for initializing command classes of a certain GeoIPS Command.
    """

    def __init__(self, parent=None, legacy=False):
        """Initialize GeoipsCommand with a subparser and default to the command func.

        Do this for each GeoipsCLI.geoips_command_classes. This will instantiate
        each subcommand class with a parser and point towards the correct default
        function to call if that subcommand has been called.

        Parameters
        ----------
        parent: optional - GeoipsCommand Class
            - The parent command class that possibly is initializing it's child.
              Ex. GeoipsList would invoke this init function for each of its subcommand
              classes (GeoipsListPackages, GeoipsListScripts, ...). When it invokes this
              init, it supplies 'self' as an argument to follow the correct logic below.
        legacy: optional - bool
            - Whether or not the command supplied was called in legacy mode. This only
              occurs for 'geoips run' commands, where instead of typing 'geoips run',
              the user called 'run_procflow' or 'data_fusion_procflow'. This is used for
              suppressing or displaying help information for '--procflow'.
        """
        self.legacy = legacy
        self.github_org_url = "https://github.com/NRLMMD-GEOIPS/"
        self.parent = parent
        self.alias_mapping = alias_mapping
        if self.parent:
            # Set the combined name of the provided object. For example, if this was the
            # parent 'list' command, it would be 'geoips_list'. If it was a child of
            # list, for example 'scripts', combined name would be 'geoips_list_scripts'
            self.combined_name = f"{parent.combined_name}_{self.name}"

            # We need to create a Geoips<cmd>Common Class for arguments
            # that are shared between common commands. For example, we've created
            # a 'GeoipsListCommon' class which adds arguments that will be shared
            # by each GeoipsList<cmd> class. Ie. if GeoipsListCommon has
            # arguments --package, --columns, etc., and all of those arguments
            # would be inherited by each GeoipsList<cmd>
            if "list" in self.combined_name:
                parent_parsers = [GeoipsListCommon().parser]
            else:
                parent_parsers = []

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
                # If the command's name exists w/in the alias mapping, then
                # add thoss aliases to the parser, otherwise just set it as an empty
                # list.
                aliases = self.alias_mapping.get(self.name.replace("_", "-"), [])
                # Attempt to create a sepate sub-parser for the specific command
                # class being initialized so we can separate the commands arguments
                # in a tree-like structure
                self.parser = parent.subparsers.add_parser(
                    self.name,
                    description=self.cmd_instructions["instructions"][
                        self.combined_name
                    ]["help_str"],
                    help=self.cmd_instructions["instructions"][self.combined_name][
                        "help_str"
                    ],
                    usage=self.cmd_instructions["instructions"][self.combined_name][
                        "usage_str"
                    ],
                    parents=parent_parsers,
                    conflict_handler="resolve",
                    aliases=aliases,
                    formatter_class=argparse.RawTextHelpFormatter,
                )
            except KeyError:
                raise KeyError(
                    "Error, the supplied command line instructions are improperly "
                    "formatted. You need an 'instructions' entry that contains a "
                    f"'{self.combined_name}' key."
                )
        else:
            # Otherwise initialize a top-level parser for this command.
            self.parser = argparse.ArgumentParser(
                formatter_class=argparse.RawTextHelpFormatter,
            )
            self.combined_name = self.name

        self.add_subparsers()
        self.parser.set_defaults(
            command=self.combined_name.replace("_", " "),
            command_parser=self.parser,
        )

    @property
    @abc.abstractmethod
    def name(self):
        """Name of the command class."""
        pass

    @property
    @abc.abstractmethod
    def command_classes(self):
        """List of command_classes related to the top level command.

        For example, if the class provided was GeoipsList, command_classes would
        be the list of available command_classes that "geoips list" implements.
        """
        pass

    def add_subparsers(self):
        """Add subparsers for each command class.

        This is done so we can limit the scope of what arguments are accepted for each
        geoips <cmd> command. This is only done for the top-level command, such as
        "list", "run", "get", etc.

        For example, if this were the GeoipsList Command Class, we would create a
        self.list_subparsers attribute, which we then add individual parsers for each
        command, as in interfaces, plugins, packages, scripts, etc.
        """
        if len(self.command_classes):
            self.subparsers = self.parser.add_subparsers(
                help=f"{self.name} instructions.",
            )
            for subcmd_cls in self.command_classes:
                subcmd_cls(parent=self, legacy=self.legacy)

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

    This class is a blueprint of what each executable GeoIPS Command Classes
    can implement.
    """

    def __init__(self, parent=None, legacy=False):
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
        legacy: optional - bool
            - Whether or not the command supplied was called in legacy mode. This only
              occurs for 'geoips run' commands, where instead of typing 'geoips run',
              the user called 'run_procflow' or 'data_fusion_procflow'. This is used for
              suppressing or displaying help information for '--procflow'.
        """
        super().__init__(parent=parent, legacy=legacy)
        # Since this class is exectuable (ie. not the cli, top-level list...),
        # add available arguments for that command and set that function to
        # the command's executable function (__call__) if that command is called.
        self.add_arguments()
        self.parser.set_defaults(
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
        """Add arguments related to the command class.

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

    def _get_headers_by_command(self, args, default_headers):
        """Retrieve the appropriate headers from a list command with the given args.

        Headers are the top-row of the tabular output from 'list' commands. These are
        customizable via optional args [--column, --long] and we retrieve the
        appropriate headers based on those optional arguments and the 'list' command
        provided.

        Parameters
        ----------
        args: argparse Argument Namespace
            - The arguments provided to a certain list command

        Returns
        -------
        headers: list of str
            - The list of column headers that will be outputted
        """
        columns = args.columns
        if columns:
            headers = {}
            for col in columns:
                if col not in list(default_headers.keys()):
                    err_str = (
                        f"Column header '{col}', is not a valid header. Please select "
                        "one or more of the following keys, which correspond to the "
                        f"appropriate value:\n{default_headers}"
                    )
                    self.parser.error(err_str)
                headers[col] = default_headers[col]
        else:
            # long has been set or was defaulted to; use the default headers
            headers = default_headers
        return headers

    def _print_plugins(self, interface, interface_registry, args):
        """Print the plugins under a certain interface in alongside minimal info.

        "Long Format" includes these pieces of information:
            - GeoIPS Package
            - Interface Name
            - Interface Type
            - Family
            - Plugin Name
            - Source Names
            - Relpath

        Parameters
        ----------
        interface: geoips.interfaces.<interface_type>
            - The interface we will be parsing and displaying.
        interface_registry: dict
            - The plugin registry associated with the given interface.
        args: argparse Argument Namespace
            - The arguments provided to a certain list command
        """
        default_headers = {
            "package": "GeoIPS Package",
            "interface": "Interface Name",
            "plugin_type": "Interface Type",
            "family": "Family",
            "plugin_name": "Plugin Name",
            "source_names": "Source Names",
            "relpath": "Relative Path",
        }
        headers = self._get_headers_by_command(args, default_headers)
        table_data = self._generate_table_data_by_interface(
            interface,
            interface_registry,
            headers,
        )
        print(
            tabulate(
                table_data,
                headers=headers.values(),
                tablefmt="rounded_grid",
                maxcolwidths=self.terminal_width // len(headers),
            )
        )

    def _generate_table_data_by_interface(self, interface, interface_registry, headers):
        """Generate the table data needed for output in '_print_plugins.

        Given a certain interface and a list of headers, generate a list of table data
        used for outputting information used by 'geoips list interface' and
        'geoips list plugins'.

        Parameters
        ----------
        interface: geoips.interfaces.<interface_type>
            - The interface object we will be gathering data from.
        interface_registry: dict
            - The plugin registry associated with the given interface.
        headers: dict
            - Dictionary of strings representing the key-value mapping of the
              headers we'd like to output.

        Returns
        -------
        table_data: 2D List of Strings
            - The corresponding data we will output, where each sub-list is ordered
              by headers.
        """
        table_data = []
        if interface.name == "products":
            for plugin_key in sorted(interface_registry.keys()):
                product_dict = interface_registry[plugin_key]
                table_data += self._get_entry(product_dict, headers)
        else:
            table_data += self._get_entry(interface_registry, headers)
        return table_data

    def _get_entry(self, plugin_dict, headers):
        """Generate a table of info based on the plugin and headers provided.

        Where a table of info is a 2D list of strings that represents the
        plugin x headers combination of data. Say, for product plugin yaml file
        abi.yaml, we'd loop over every product in that file, add to that product
        plugin's entry each header ('source_name', 'family', 'plugin_name', etc.) that
        was selected, and return the 2D table where each 1D list represents the info
        that corresponds to the product plugin.

        Parameters
        ----------
        plugin_dict: dict
            - The portion of the plugin_registry needed to access all plugins of a
              certain interface or all plugins of a certain product.
        headers: dict
            - Dictionary of strings representing the key-value mapping of the
              headers we'd like to output.

        Returns
        -------
        table_data: 2D list of str
            - A 2D list of strings containing information about plugins listed in the
              order of headers.keys()
        """
        table_data = []
        for plugin_key in list(plugin_dict.keys()):
            plugin_entry = []
            for header in list(headers.keys()):
                if (
                    header == "source_names"
                    and plugin_dict[plugin_key]["interface"] != "products"
                ):
                    plugin_entry.append("N/A")
                elif (
                    header == "family"
                    and plugin_dict[plugin_key]["interface"] == "products"
                ):
                    plugin_entry.append("N/A")
                elif header == "plugin_name":
                    plugin_entry.append(plugin_key)
                else:
                    plugin_entry.append(plugin_dict[plugin_key][header])
            table_data.append(plugin_entry)
        return table_data


class GeoipsListCommon(GeoipsExecutableCommand):
    """Class containing common optional arguments shared between list commands."""

    name = "list_common"
    command_classes = []

    def add_arguments(self):
        """Add arguments to the list-subparser for the List Command."""
        self.parser.add_argument(
            "--package_name",
            "-p",
            type=str,
            default="all",
            choices=self.plugin_package_names,
            help="The GeoIPS package to list from.",
        )
        mutex_group = self.parser.add_mutually_exclusive_group()
        mutex_group.add_argument(
            "--long",
            "-l",
            default=True,
            action="store_true",
            help="Flag representing the 'long' listing of a certain command.",
        )
        mutex_group.add_argument(
            "--columns",
            "-c",
            type=str,
            nargs="+",
            default=None,
            help="""Specific Headers of Data you'd like to see listed.
                    For more in formation on headers available, run
                    'geoips list <cmd> <positional_args> --columns help'.
                    """,
        )

    def __call__(self, args):
        """Exectutable function for GeoipsListCommon Class. Not implemented."""
        pass


class CommandClassFactory:
    """An abstract class factory for creating CLI-based Command Classes.

    This architecture can be used to generate CLI command classes for specific use
    cases. A couple which we'll implement early on is are:

    * GeoipsListSingleInterface:

        * GeoipsListSingleInterfaceAlgorithms
        * GeoipsListSingleInterfaceColormappers
        * ...
        * GeoipsListSingleInterfaceTitleFormatters

    * GeoipsGetInterface

        * GeoipsGetInterfaceAlgorithm
        * GeoipsGetInterfaceColormapper
        * ...
        * GeoipsGetInterfaceTitleFormatter

    This class has been created to reduce the verbosity of geoips commands without
    having to copy-paste classes specifc to a certain interface.
    """

    def __init__(self, base_class, class_name, add_attrs={}):
        """Initialize the class factory and generate a class derived from base_class.

        Parameters
        ----------
        base_class: Class
            - The base class to build each generated class with..
            - Ie. if we were creating a class factory for GeoipsListSingleInterface, the
              base class would be 'GeoipsListSingleInterface'.
        class_name: str
            - The name of the class that we'd like to generate.
            - Ie. if we were creating a class factory for GeoipsListSingleInterface, the
              class to generate would be a strign that represents all the class for the
              associated interface we'd like to generate ('algorithms', ...).
            - The classes would then look like:
                - "GeoipsListAlgorithms"
                - "GeoipsListColormappers"
                - ...
                - "<base_class_name><class_name>"
        add_attrs: dict (optional)
            - A dictionary of attributes we'd like to assign to each command class
            - If specified and has overlapping keys to those specified below, this
              dictionary will override the defaults.
        """
        self.base_class = base_class
        self.base_class_name = self.base_class.__name__
        default_attrs = {
            "name": class_name,
            "command_classes": [],
            "add_arguments": base_class.add_arguments,
            "__call__": base_class.__call__,
        }
        # Combine with additional attributes, overwriting defaults where applicable.
        class_attrs = {**default_attrs, **add_attrs}
        # Add the class of <base_class_name><class_name> to the constructors 'classes'
        # attribute. Don't actually initialize these classes as we'll be doing that
        # later once we have the required information.
        self.generated_class = type(
            f"{self.base_class_name}{class_name.title().replace('_', '')}",
            (base_class,),
            class_attrs,
        )
