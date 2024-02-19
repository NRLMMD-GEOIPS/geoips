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
from os.path import basename

setup_logging()
LOG = logging.getLogger(__name__)

class CLI:
    """GeoIPS Command Line Interface."""

    def __init__(self):
        """Entry point for GeoIPS command line interface (CLI)."""
        self._parser = argparse.ArgumentParser()
        self._subparser = self._parser.add_subparsers(help="sub-parser help")
        self._parser_list = self._subparser.add_parser("list", help="list instructions")
        self._parser_list.set_defaults(exe_command=self.list)
        # Parser for list commands. What should we be able to list?
        # Ideas: All Interfaces, all plugins within an interface, ...
        available_list_options = interfaces.__all__ + ["interfaces"] + [
            str(pkg_name) for pkg_name in self.plugin_packages
        ]
        self._parser_list.add_argument(
            "list_options",
            type=str.lower,
            default="interfaces",
            choices=available_list_options,
        )
        # Parser for the run commands. Currently we implement:
        # `geoips run <pkg_name> <script_name.sh>`
        self._parser_run = self._subparser.add_parser("run", help="run instructions")
        self._parser_run.set_defaults(exe_command=self.run)
        self._parser_run.add_argument(
            "pkg_name",
            type=str.lower,
            default="geoips",
            choices=self.plugin_packages,
        )
        self._parser_run.add_argument(
            "script_name",
            type=str,
            default="abi.static.Visible.imagery_annotated.sh",
        )
        self.GEOIPS_ARGS = self._parser.parse_args()

    @property
    def plugin_packages(self):
        """Plugin Packages property of the CLI."""
        return [
            ep.value for ep in get_entry_point_group("geoips.plugin_packages")
        ]

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
        # interface_name is the interface to list off, or all of the interfaces to list
        # interface_name = args.list_options
        if to_be_listed in self.plugin_packages:
            # If the first command is a package name, this will be used to list scripts
            self.list_package_scripts(to_be_listed)
        else:
            self.list_interface(to_be_listed)

    def list_package_scripts(self, package_name):
        """List all of the available scripts held under <package_name>.

        Parameters
        ----------
        package_name: str
            - The GeoIPS Package name whose scripts you want to list.
        """
        script_names = sorted(
            [
                basename(fpath) for fpath in
                    glob(
                        str(resources.files(package_name) / "../tests/scripts" / "*.sh")
                    )
            ]
        )
        LOG.interactive("-" * len(f"{package_name.title()} Available Scripts"))
        LOG.interactive(f"{package_name.title()} Available Scripts")
        LOG.interactive("-" * len(f"{package_name.title()} Available Scripts"))
        LOG.interactive(f"{script_names}\n")

    def list_interface(self, interface_name):
        """List the available interface[s] and their corresponding plugin names.

        Parameters
        ----------
        interface_name: str
            - The name of the interface to list. If name == "interfaces" list all available
            interfaces and their plugin names.
        """
        if interface_name != "interfaces":
            interfaces_to_list = [getattr(interfaces, interface_name)]
        else:
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
            LOG.interactive("-" * len(curr_interface.name))
            LOG.interactive(curr_interface.name)
            LOG.interactive("-" * len(curr_interface.name))
            LOG.interactive(", ".join(sorted(interface_registry.keys())) + "\n")

    def execute_command(self):
        """Execute the given command."""
        self.GEOIPS_ARGS.exe_command(self.GEOIPS_ARGS)


def main():
    """Entry point for GeoIPS command line interface (CLI)."""
    geoips_cli = CLI()
    geoips_cli.execute_command()


if __name__ == "__main__":
    main()

