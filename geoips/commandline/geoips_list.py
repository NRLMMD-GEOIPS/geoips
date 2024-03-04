"""GeoIPS CLI "list" command.

Lists the appropriate plugins/interfaces based on the arguments provided.
"""
from glob import glob
from importlib import resources, import_module
import json
from os.path import basename
import sys
from tabulate import tabulate

from geoips.commandline.commandline_interface import GeoipsCommand
from geoips import interfaces


class GeoipsListInterfaces(GeoipsCommand):
    """GeoipsListInterfaces Sub-Command Class.

    Called via `geoips list-interfaces`. Outputs the following data in a tabular format.

    Data Output
    -----------
    out_array: 2D Array of Data
        - [
            package, interface_name, interface_type, supported_families,
            short_docstring, filepath, documentation_link
        ]
    """
    subcommand_name = "list-interfaces"
    subcommand_classes = []

    def add_arguments(self):
        self.subcommand_parser.add_argument(
            "--implemented",
            "-i",
            default=False,
            action="store_true",
            help=str(
                "Flag to list what's implemented in each package, " +
                "rather than what's available."
            ),
        )
        self.subcommand_parser.add_argument(
            "--package",
            "-p",
            type=str,
            default="all",
            choices=self.plugin_packages,
            help="The GeoIPS package to list from, defaults to all packages",
        )

    def list_interfaces(self, args):
        """List the available interface[s] within [a] GeoIPS Package[s]".

        Data Output
        -----------
        out_array: 2D Array of Data
            - [
                package, interface_name, interface_type, supported_families,
                short_docstring, filepath, documentation_link
            ]

        Parameters
        ----------
        args: Argparse Namespace()
            - The Argument Namespace for GeoipsListInterfaces Sub-Command
        """
        package_name = args.package
        # Flag representing whether or not we want to list what's implemented or
        # what's available.
        implemented = args.implemented
        if implemented:
            self.list_implemented_interfaces(package_name)
        else:
            self.list_available_interfaces()

    def list_available_interfaces(self):
        """List the available interface[s] within [a] GeoIPS Package[s]".

        Data Output
        -----------
        out_array: 2D Array of Data
            - [
                package, interface_name, interface_type, supported_families,
                short_docstring, filepath, documentation_link
            ]
        """
        interface_data = []
        for interface_name in interfaces.__all__:
            interface = getattr(interfaces, interface_name)
            interface_data.append(
                [
                    "geoips",
                    interface.interface_type,
                    interface_name,
                    interface.supported_families,
                    interface.__doc__.split("\n")[0],
                    str(
                        resources.files("geoips") /
                        f"interfaces/{interface.interface_type}/{interface.name}.py"
                    ),
                ],
            )
        print("-" * len("GeoIPS Interfaces"))
        print("GeoIPS Interfaces")
        print("-" * len("GeoIPS Interfaces"))
        print(
            tabulate(
                interface_data,
                headers=[
                    "Package", "Interface Type", "Interface Name",
                    "Supported Families", "Docstring", "Abspath",
                ],
                tablefmt="rounded_grid",
            )
        )

    def list_implemented_interfaces(self, package_name):
        """List the implemented interface[s] within [a] GeoIPS Package[s].

        Ie. search through all, or an individual package and list off what has been
        implemented in such package[s].

        Data Output
        -----------
        out_array: 2D Array of Data
            - [
                package, interface_name, interface_type, supported_families,
                short_docstring, filepath, documentation_link
            ]

        Parameters
        ----------
        package_name: str
            - The GeoIPS Package name whose scripts you want to list.
        """
        for plugin_package_name, pkg_path in \
            zip(self.plugin_packages, self.plugin_package_paths):

            if package_name == "all" or package_name == plugin_package_name:
                pkg_registry = json.load(
                    open(
                        f"{pkg_path}/{plugin_package_name}/registered_plugins.json", "r"
                    )
                )
            else:
                continue
            interface_data = []
            for interface_type in pkg_registry.keys():
                for interface_name in pkg_registry[interface_type].keys():
                    interface_data.append(
                        [plugin_package_name, interface_type, interface_name]
                    )
            print("-" * len(f"{plugin_package_name.title()} Interfaces"))
            print(f"{plugin_package_name.title()} Interfaces")
            print("-" * len(f"{plugin_package_name.title()} Interfaces"))
            print(
                tabulate(
                    interface_data,
                    headers=["GeoIPS Package", "Interface Type", "Interface Name"],
                    tablefmt="rounded_grid",
                )
            )


class GeoipsListPackages(GeoipsCommand):
    """GeoipsListInterfaces Sub-Command Class.

    Called via `geoips list-interfaces`. Outputs the following data in a tabular format.

    Data Output
    -----------
    out_array: 2D Array of Data
        - [
            package, interface_name, interface_type, supported_families,
            short_docstring, filepath, documentation_link
        ]
    """
    subcommand_name = "list-packages"
    subcommand_classes = []

    def add_arguments(self):
        pass

    def list_packages(self, args):
        """List all of the available GeoIPS Packages.

        Only installed packages will be listed. Ie, if geoips_clavrx, or another
        suitable package exists, but is not installed, it will not be listed.

        Data Output
        -----------
        output_array: 2D Array
            - [
                package, docstring, filepath, documentation_link
            ]

        Parameters
        ----------
        args: Argparse Namespace()
            - The Argument Namespace for GeoipsListPackages Sub-Command
        """
        pkg_data = []
        for package_name, package_path in \
            zip(self.plugin_packages, self.plugin_package_paths):

            docstring = import_module(package_name).__doc__
            pkg_data.append(
                [
                    package_name,
                    docstring,
                    package_path,
                ],
            )
        print("-" * len(f"GeoIPS Packages"))
        print(f"GeoIPS Packages")
        print("-" * len(f"GeoIPS Packages"))
        print(
            tabulate(
                pkg_data,
                headers=["GeoIPS Package", "Docstring", "Package Path"],
                tablefmt="rounded_grid",
            )
        )


class GeoipsListPlugins(GeoipsCommand):
    """GeoipsListInterfaces Sub-Command Class.

    Called via `geoips list-interfaces`. Outputs the following data in a tabular format.

    Data Output
    -----------
    out_array: 2D Array of Data
        - [
            package, interface_name, interface_type, supported_families,
            short_docstring, filepath, documentation_link
        ]
    """
    subcommand_name = "list-plugins"
    subcommand_classes = []

    def add_arguments(self):
        self.subcommand_parser.add_argument(
            "--package",
            "-p",
            type=str,
            default="all",
            choices=self.plugin_packages,
            help="The GeoIPS package to list from, defaults to all packages",
        )

    def list_plugins(self, args):
        """List the available interface[s] and their corresponding plugin names.

        Parameters
        ----------
        args: Argparse Namespace()
            - The list argument namespace to parse through
        """
        package_name = args.package
        # List of every available interface
        interfaces_to_list = [
            getattr(interfaces, name) for name in sorted(interfaces.__all__)
        ]

        for curr_interface in interfaces_to_list:
            interface_registry = self._get_registry_by_interface_and_package(
                curr_interface, package_name
            )
            # Interface Registry can be None if we are looking through a specific
            # package whose registry doesn't contain that certain interface.
            if interface_registry is None:
                continue
            print("-" * len(curr_interface.name))
            print(curr_interface.name)
            print("-" * len(curr_interface.name))
            self._print_plugins_short_format(curr_interface, interface_registry)


class GeoipsListScripts(GeoipsCommand):
    """GeoipsListInterfaces Sub-Command Class.

    Called via `geoips list-interfaces`. Outputs the following data in a tabular format.

    Data Output
    -----------
    out_array: 2D Array of Data
        - [
            package, interface_name, interface_type, supported_families,
            short_docstring, filepath, documentation_link
        ]
    """
    subcommand_name = "list-scripts"
    subcommand_classes = []

    def add_arguments(self):
        self.subcommand_parser.add_argument(
            "--package",
            "-p",
            type=str,
            default="all",
            choices=self.plugin_packages,
            help="The GeoIPS package to list from.",
        )

    def list_scripts(self, args):
        """List all of the available scripts held under <package_name>.

        Parameters
        ----------
        args: Namespace()
            - The list argument namespace to parse through
        """
        package_name = args.package
        if package_name == "all":
            plugin_packages = self.plugin_packages
        else:
            plugin_packages = [package_name]
        for plugin_package_name in plugin_packages:
            script_names = sorted(
                [
                    [plugin_package_name, basename(fpath)] for fpath in
                        glob(
                            str(
                                resources.files(plugin_package_name) /
                                "../tests/scripts" / "*.sh"
                            )
                        )
                ]
            )
            print("-" * len(f"{plugin_package_name.title()} Available Scripts"))
            print(f"{plugin_package_name.title()} Available Scripts")
            print("-" * len(f"{plugin_package_name.title()} Available Scripts"))
            print(
                tabulate(
                    script_names,
                    headers=["GeoIPS Package", "Filename"],
                    tablefmt="rounded_grid",
                )
            )

class GeoipsList(GeoipsCommand):
    """GeoipsList Sub-Command for listing packages/scripts/interfaces/plugins."""
    subcommand_name = "list"
    subcommand_classes = [
        GeoipsListInterfaces, GeoipsListPackages, GeoipsListPlugins, GeoipsListScripts
    ]

    def add_arguments(self):
        """Instantiate the valid arguments that are supported for the list command.

        Currently the "geoips list" command supports this format:
            - geoips list <to_be_listed> -p <package_name>
        Where:
            <to_be_listed> is any of the strings in self.available_list_options
            <package_name> is any GeoIPS package that is installed and recognized by the
              GeoIPS Libarary
        """
        # pass
        self.subcommand_parser.add_argument(
            "interface_name",
            type=str.lower,
            default="algorithms",
            choices=interfaces.__all__,
            help="GeoIPS Interfaces to list plugins_from"
        )
        self.subcommand_parser.add_argument(
            "--package",
            "-p",
            type=str,
            default="all",
            choices=self.plugin_packages,
            help="The GeoIPS package to list from.",
        )

    def list(self, args):
        """List all elements of the selected list option.

        Selected list option is args.interface_name, where interface_name can be any of:
            - any geoips.interface
        Where any of those options can be GeoIPS Package specific or from any package.

        Parameters
        ----------
        args: Namespace()
            - The list argument namespace to parse through
        """
        interface_name = args.interface_name
        package_name = args.package
        interface = getattr(interfaces, interface_name)
        interface_registry= self._get_registry_by_interface_and_package(
            interface, package_name
        )
        # Interface Registry can be None if we are looking through a specific
        # package whose registry doesn't contain that certain interface.
        if interface_registry is None:
            info_str = f"No plugins found under interface `{interface_name}` under "
            info_str += f"package `{package_name}`."
            print(info_str)
        else:
            print("-" * len(interface_name))
            print(interface_name)
            print("-" * len(interface_name))
            self._print_plugins_short_format(interface, interface_registry)