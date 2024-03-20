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
from shutil import get_terminal_size
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
        self.parent = parent
        if self.parent:
            if self.parent.subcommand_name == "cli":
                combined_name = self.subcommand_name
                parent_parsers = []
            else:
                combined_name = f"{self.parent.subcommand_name} {self.subcommand_name}"
                # We need to create a Geoips<cmd>Common Class for arguments
                # that are shared between common commands. For example, we've created
                # a 'GeoipsListCommon' class which adds arguments that will be shared
                # by each GeoipsList<sub-cmd> class. Ie. if GeoipsListCommon has
                # arguments --package, --columns, etc., and all of those arguments
                # would be inherited by each GeoipsList<sub-cmd>
                if "list" in combined_name:
                    parent_parsers = [GeoipsListCommon().subcommand_parser]
                else:
                    parent_parsers = []
            self.subcommand_parser = self.parent.subparsers.add_parser(
                name=self.subcommand_name,
                description=self.cmd_instructions[combined_name]["help_str"],
                help=self.cmd_instructions[combined_name]["help_str"],
                usage=self.cmd_instructions[combined_name]["usage_str"],
                parents=parent_parsers,
                conflict_handler="resolve",
            )
        else:
            self.subcommand_parser = argparse.ArgumentParser()
            combined_name = self.subcommand_name
        if hasattr(self, "__call__"):
            # If the subcommand class is exectuable (ie. not the cli, top-level list...)
            # Then add available arguments for that command and set that function to
            # the commands executable function (__call__) if that command is called.
            self.add_arguments()
            self.subcommand_parser.set_defaults(
                exe_command=self.__call__,
            )
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
                help=f"{self.subcommand_name} instructions.",
                # title=f"{self.subcommand_name} actions.",
            )
            # self.subparsers.required = True
            # self.subparsers.dest = self.subcommand_name
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
            self._plugin_package_paths = [
                dirname(resources.files(ep.value))
                for ep in get_entry_point_group("geoips.plugin_packages")
            ]
        return self._plugin_package_paths


class GeoipsExecutableCommand(GeoipsCommand):
    """GeoipsExecutableCommand Abstract Base Class.

    This class is a blueprint of what each executable GeoIPS Sub-Command Classes
    can implement.
    """

    @property
    def terminal_width(self):
        """The Width in ANSI-Characters of the User's Terminal.

        Generate this every time as the screen width may change during usage.
        """
        return get_terminal_size().columns

    @property
    def test_dataset_dict(self):
        """Dictionary mapping of GeoIPS Test Datasets.

        Mapping goes {"test_dataset_name": "test_dataset_url"}
        """
        if not hasattr(self, "_test_dataset_urls"):
            self._test_dataset_dict = {
                "test_data_viirs": "https://io.cira.colostate.edu/s/mQ2HbE2Js4E9rba/download/test_data_viirs.tgz",  # noqa
                "test_data_smap": "https://io.cira.colostate.edu/s/CezXWwXg4qR2b94/download/test_data_smap.tgz",  # noqa
                "test_data_scat": "https://io.cira.colostate.edu/s/HyHLZ9F8bnfcTcd/download/test_data_scat.tgz",  # noqa
                "test_data_sar": "https://io.cira.colostate.edu/s/snxx8S5sQL3AL7f/download/test_data_sar.tgz",  # noqa
                "test_data_noaa_aws": "https://io.cira.colostate.edu/s/fkiPS3jyrQGqgPN/download/test_data_noaa_aws.tgz",  # noqa
                "test_data_gpm": "https://io.cira.colostate.edu/s/LT92NiFSA8ZSNDP/download/test_data_gpm.tgz",  # noqa
                "test_data_fusion": "https://io.cira.colostate.edu/s/DSz2nZsiPMDeLEP/download/test_data_fusion.tgz",  # noqa
                "test_data_clavrx": "https://io.cira.colostate.edu/s/ACLKdS2Cpgd2qkc/download/test_data_clavrx.tgz",  # noqa
                "test_data_amsr2": "https://io.cira.colostate.edu/s/FmWwX2ft7KDQ8N9/download/test_data_amsr2.tgz",  # noqa
            }
        return self._test_dataset_dict

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

    def _get_headers_by_command(self, args, default_headers):
        """Retrieve the appropriate headers from a list command with the given args.

        Headers are the top-row of the tabular output from 'list' commands. These are
        customizable via optional args [--column, --short, --long] and we retrieve
        the appropriate headers based on those optional arguments and the 'list' command
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
                    err_str = f"Column header '{col}', is not a valid header. Please "
                    err_str += f"select one or more of the following keys, which "
                    err_str += "correspond to the appropriate value:\n"
                    err_str += f"{default_headers}"
                    self.subcommand_parser.error(err_str)
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
            interface, interface_registry, headers,
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
        """Generate the table data needed for output in '_print_plugins_short_format.

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
        """Retrieve the appropriate plugin entry given a list of valid headers.

        Parameters
        ----------
        plugin_dict: dict
            - The portion of the plugin_registry needed to access the appropriate plugin
        headers: dict
            - Dictionary of strings representing the key-value mapping of the
              headers we'd like to output.

        Returns
        -------
        plugin_entry: list of str
            - A list of strings containing information about a plugin listed in the
              order of headers.keys()
        """
        table_data = []
        for plugin_key in list(plugin_dict.keys()):
            plugin_entry = []
            for header in list(headers.keys()):
                if (
                    header == "source_names" and
                    plugin_dict[plugin_key]["interface"] != "products"
                ):
                    plugin_entry.append("N/A")
                elif (
                    header == "family" and
                    plugin_dict[plugin_key]["interface"] == "products"
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

    subcommand_name = "list"
    subcommand_classes = []

    def add_arguments(self):
        """Add arguments to the list-subparser for the List Command."""
        self.subcommand_parser.add_argument(
            "--package_name",
            "-p",
            type=str,
            default="all",
            choices=self.plugin_packages,
            help="The GeoIPS package to list from.",
        )
        mutex_group = self.subcommand_parser.add_mutually_exclusive_group()
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
            nargs='+',
            default=None,
            help="Specific Headers of Data you'd like to see listed.",
        )

    def __call__(self, args):
        pass