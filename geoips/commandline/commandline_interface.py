"""Code to implement GeoIPS Command Line Interface (CLI).

Will implement a plethora of commands, but for the meantime, we'll work on
'geoips list' and 'geoips run'
"""

import argparse
from geoips import interfaces
import logging
from geoips.commandline.log_setup import setup_logging
from geoips.geoips_utils import get_entry_point_group
from importlib import resources
from subprocess import call
from glob import glob
from os.path import basename, dirname
# from pathlib import Path
from tabulate import tabulate

setup_logging()
LOG = logging.getLogger(__name__)


class GeoipsArgParser:
    """GeoIPS Argument Parser Class for the CLI."""

    def __init__(self):
        """Initialize the GeoIPS Argument Parser."""
        # List of every installed GeoIPS package
        self._plugin_packages = self.plugin_packages
        self._plugin_package_paths = self.plugin_package_paths
        self._available_list_options = self.available_list_options
        # Parser to handle commands
        self._parser = self.parser
        self._subparser = self.subparser
        # Parser for list commands. What should we be able to list?
        # Ideas: All Interfaces, all plugins within an interface, ...
        self._parser_list = self.parser_list
        # Parser for the run commands. Currently we implement:
        # `geoips run <pkg_name> <script_name.sh>`
        self._parser_run = self.parser_run

    @property
    def plugin_package_paths(self):
        """Plugin Package Paths property of the CLI."""
        if not hasattr(self, "_plugin_package_paths"):
            return [
                dirname(resources.files(ep.value)) \
                    for ep in get_entry_point_group("geoips.plugin_packages")
            ]
        else:
            return self._plugin_package_paths

    @property
    def plugin_packages(self):
        """Plugin Packages property of the CLI."""
        if not hasattr(self, "_plugin_packages"):
            return [
                ep.value for ep in get_entry_point_group("geoips.plugin_packages")
            ]
        else:
            return self._plugin_packages

    @property
    def available_list_options(self):
        """List of available Lower-Level GeoIPS Software that can be listed off."""
        if not hasattr(self, "_available_list_options"):
            return interfaces.__all__ + ["interfaces", "packages"] + [
                str(pkg_name) for pkg_name in self.plugin_packages
            ]
        else:
            return self._available_list_options

    @property
    def parser(self):
        """The Main ArgumentParser Instance for the CLI."""
        if not hasattr(self, "_parser"):
            return argparse.ArgumentParser()
        else:
            return self._parser

    @property
    def subparser(self):
        """The Argparse Subparser Instance for the CLI."""
        if not hasattr(self, "_subparser"):
            self._subparser = self.parser.add_subparsers(help="sub-parser help")
            return self._subparser
        else:
            return self._subparser

    @property
    def parser_list(self):
        """Subparser for the 'List' Command.

        'List' Capabilities
        -------------------
            - geoips list packages
                - lists all available GeoIPS Packages
            - geoips list interfaces
                - lists all available GeoIPS Interfaces
            - geoips list plugins
                - list all available plugins from every interface of every package
            - geoips list scripts
            - geoips list <interface_name>
                - Lists all plugins under a certain interface (ie. algorithms)
            - geoips list <what_to_list> -p <package_name>
                - Lists <what_to_list> out of GeoIPS Package <package_name>
        """
        if not hasattr(self, "_parser_list"):
            self._parser_list = self.subparser.add_parser(
                "list", help="list instructions"
            )
            self._parser_list.add_argument(
                "list_options",
                type=str.lower,
                default="interfaces",
                choices=self.available_list_options,
                help="GeoIPS lower level plugins/interfaces/scripts to list off."
            )
            self._parser_list.add_argument(
                "--verbose",
                "-v",
                default=False,
                action="store_true",
                help="List in a verbose fashion.",
            )
            self._parser_list.add_argument(
                "--package",
                "-p",
                choices=self.plugin_packages,
                help="The GeoIPS package to list from.",
            )
            return self._parser_list
        else:
            return self._parser_list

    @property
    def parser_run(self):
        """The Run Subparser Instance for the CLI."""
        if not hasattr(self, "_parser_run"):
            self._parser_run = self.subparser.add_parser(
                "run", help="run instructions"
            )
            self._parser_run.add_argument(
                "pkg_name",
                type=str.lower,
                default="geoips",
                choices=self.plugin_packages,
                help="GeoIPS Package to run a script from."
            )
            self._parser_run.add_argument(
                "script_name",
                type=str,
                default="abi.static.Visible.imagery_annotated.sh",
                help="Script to run from previously selected package."
            )
            return self._parser_run
        else:
            return self._parser_run


class CLI(GeoipsArgParser):
    """GeoIPS Command Line Interface."""

    def __init__(self):
        """Entry point for GeoIPS command line interface (CLI)."""
        super().__init__()
        self.parser_list.set_defaults(exe_command=self.list)
        self.parser_run.set_defaults(exe_command=self.run)
        self.GEOIPS_ARGS = self.parser.parse_args()

    def run(self, args):
        """Run the provided GeoIPS command.

        Parameters
        ----------
        args: Namespace()
            - The argument namespace to parse through
        """
        pkg_name = args.pkg_name
        script_name = args.script_name
        script_path = str(resources.files(pkg_name) / "../tests/scripts" / script_name)
        output = call(script_path, shell=True)
        return output

    def list(self, args):
        """List the provided interface all plugin names that exist beneath it.

        Parameters
        ----------
        args: Namespace()
            - The argument namespace to parse through
        """
        # Variable below will be used to list scripts available in a certain package,
        # Full product definitions, call signatures, etc.
        # We will need to create sub classes that implement list_interfaces,
        # list_scripts, ..., same needs to be done for "run" function

        to_be_listed = args.list_options
        if to_be_listed == "packages":
            self.list_packages(args.verbose)
        elif to_be_listed in self.plugin_packages:
            # If the first command is a package name, this will be used to list scripts
            self.list_package_scripts(to_be_listed, args.verbose)
        else:
            self.list_interface(to_be_listed, args.verbose)

    def list_packages(self, verbose=False):
        """List all of the available GeoIPS Packages.

        Parameters
        ----------
        verbose: bool
            - Flag which denotes whether or not we should list verbosely (add. info).
        """
        script_names = sorted(
            [
                [package_name, package_path] for package_name, package_path in \
                    zip(self.plugin_packages, self.plugin_package_paths)
            ]
        )
        print("-" * len(f"GeoIPS Packages"))
        print(f"GeoIPS Packages")
        print("-" * len(f"GeoIPS Packages"))
        print(
            tabulate(
                script_names,
                headers=["GeoIPS Package", "Package Path"],
                tablefmt="rounded_grid",
            )
        )
        # print(f"{script_names}\n")

    def list_package_scripts(self, package_name, verbose=False):
        """List all of the available scripts held under <package_name>.

        Parameters
        ----------
        package_name: str
            - The GeoIPS Package name whose scripts you want to list.
        verbose: bool
            - Flag which denotes whether or not we should list verbosely (add. info).
        """
        script_names = sorted(
            [
                [package_name, basename(fpath)] for fpath in
                    glob(
                        str(resources.files(package_name) / "../tests/scripts" / "*.sh")
                    )
            ]
        )
        print("-" * len(f"{package_name.title()} Available Scripts"))
        print(f"{package_name.title()} Available Scripts")
        print("-" * len(f"{package_name.title()} Available Scripts"))
        print(
            tabulate(
                script_names,
                headers=["GeoIPS Package", "Filename"],
                tablefmt="rounded_grid",
            )
        )
        # print(f"{script_names}\n")

    def list_interface(self, interface_name, verbose=False):
        """List the available interface[s] and their corresponding plugin names.

        Parameters
        ----------
        interface_name: str
            - The name of the interface to list. If name == "interfaces" list all
              available interfaces and their plugin names.
        verbose: bool
            - Flag which denotes whether or not we should list verbosely (add. info).
        """
        if interface_name != "interfaces":
            # if the provided name != interfaces, this means we have been given a single
            # interface. Grab that interface and move on.
            interfaces_to_list = [getattr(interfaces, interface_name)]
        else:
            # List of every available interface
            interfaces_to_list = [
                getattr(interfaces, name) for name in sorted(interfaces.__all__)
            ]

        for curr_interface in interfaces_to_list:
            if curr_interface.name in interfaces.module_based_interfaces:
                plugin_type = "module_based"
            else:
                plugin_type = "yaml_based"
            interface_registry = curr_interface.plugin_registry.registered_plugins[
                plugin_type
            ][curr_interface.name]
            print("-" * len(curr_interface.name))
            print(curr_interface.name)
            print("-" * len(curr_interface.name))
            if not verbose:
                # print(f"{sorted(interface_registry.keys())}\n")
                table_data = [
                    [curr_interface.name, plugin_key] \
                    for plugin_key in sorted(interface_registry.keys())
                ]
                for plugin_entry in table_data:
                    plugin_key = plugin_entry[1]
                    if curr_interface.name == "products":
                        plugin_entry.insert(0, "Not Implemented")
                        plugin_entry.insert(2, "list")
                        plugin_entry.append("Not Implemented")
                    else:
                        plugin_entry.insert(
                            0, interface_registry[plugin_key]["package"]
                        )
                        plugin_entry.insert(
                            2, interface_registry[plugin_key]["family"]
                        )
                        plugin_entry.append(
                            interface_registry[plugin_key]["relpath"]
                        )
                print(
                    tabulate(
                        table_data,
                        headers=[
                            "GeoIPS Package",
                            "Interface",
                            "Family",
                            "Plugin Name",
                            "Relative Path",
                        ],
                        tablefmt="rounded_grid",
                    )
                )
                # print(", ".join(sorted(interface_registry.keys())) + "\n")
            else:
                self.list_interface_verbosely(
                    curr_interface, interface_registry, plugin_type
                )

    def list_interface_verbosely(self, curr_interface, interface_registry, p_type):
        """List the Provided Interface Verbosely, based on the type of interface.

        Parameters
        ----------
        curr_interface: GeoIPS BaseYamlInterface / BaseModuleInterface
            - The current interface to list verbosely.
        interface_registry: dict
            - The plugin registry dictionary associated with the current interface.
        p_type: str
            - The Plugin Type of the Interface ("module_based" or "yaml_based")
        """
        for plugin_name in sorted(interface_registry.keys()):
            # Products have a different implementation currently, so we need to handle
            # those plugins differently when listing them off.
            if curr_interface.name != "products":
                plugin_dict = {
                    "interface": curr_interface.name,
                    "family": interface_registry[plugin_name]["family"],
                    "docstring": interface_registry[plugin_name]["docstring"],
                }
                if p_type == "module_based":
                    plugin_dict["signature"] = interface_registry[plugin_name][
                        "signature"
                    ]
            else:
                # This is how products are verbosely handled. We will need to modify
                # this portion when PR "423 Test All Product Families" is merged in,
                # as that branch stores product plugins in a format of
                # <source_name>.<subplg_name>
                plugin_dict = {
                    "source_name": plugin_name,
                    "subplugin_names": sorted(interface_registry[plugin_name].keys()),
                }
            print(f"{plugin_name}: {plugin_dict}")

    def execute_command(self):
        """Execute the given command."""
        self.GEOIPS_ARGS.exe_command(self.GEOIPS_ARGS)


def main():
    """Entry point for GeoIPS command line interface (CLI)."""
    geoips_cli = CLI()
    geoips_cli.execute_command()


if __name__ == "__main__":
    main()

