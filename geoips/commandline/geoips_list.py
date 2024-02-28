
from glob import glob
from importlib import resources
import json
from os.path import basename
from tabulate import tabulate

from geoips.commandline.cli_v2 import GeoipsCommand
from geoips import interfaces


class GeoipsList(GeoipsCommand):
    """GeoipsList Sub-Command for listing packages/scripts/interfaces/plugins."""
    subcommand_name = "list"

    @property
    def available_list_options(self):
        """List of available Lower-Level GeoIPS Software that can be listed off.

        Currently, this list comprises every GeoIPS interface, "interfaces", "packages",
        "plugins", and "scripts".
        """
        if not hasattr(self, "_available_list_options"):
            self._available_list_options = sorted(
                interfaces.__all__ + ["interfaces", "packages", "plugins", "scripts"]
            )
            return self._available_list_options
        else:
            return self._available_list_options

    def add_arguments(self):
        """Instantiate the valid arguments that are supported for the list command.

        Currently the "geoips list" command supports this format:
            - geoips list <to_be_listed> -p <package_name>
        Where:
            <to_be_listed> is any of the strings in self.available_list_options
            <package_name> is any GeoIPS package that is installed and recognized by the
              GeoIPS Libarary
        """
        self.subcommand_parser.add_argument(
            "to_be_listed",
            type=str.lower,
            default="packages",
            choices=self.available_list_options,
            help="GeoIPS lower-level packages/plugins/interfaces/scripts to list off."
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

        Selected list option is args.to_be_listed, where to_be_listed can be any of:
            - any geoips.interface
            - "interfaces"
            - "packages"
            - "scripts"
            - "plugins"
        Where any of those options can be GeoIPS Package specific or from any package.

        Parameters
        ----------
        args: Namespace()
            - The list argument namespace to parse through
        """
        to_be_listed = args.to_be_listed
        if to_be_listed == "packages":
            # List the available GeoIPS packages and the paths to each package
            self.list_packages()
        elif to_be_listed == "scripts":
            # If the first command is a package name, this will be used to list scripts
            self.list_scripts(args.package)
        elif to_be_listed == "interfaces":
            # List the Available Interfaces within [a] given GeoIPS Package[s]
            self.list_interfaces(args.package)
        else:
            # List plugins within all / the provided interface name within [a] given
            # GeoIPS package[s]
            self.list_plugins(to_be_listed, args.package)

    def list_packages(self):
        """List all of the available GeoIPS Packages.

        Only installed packages will be listed. Ie, if geoips_clavrx, or another
        suitable package exists, but is not installed, it will not be listed.
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

    def list_scripts(self, package_name="all"):
        """List all of the available scripts held under <package_name>.

        Parameters
        ----------
        package_name: str
            - The GeoIPS Package name whose scripts you want to list.
        """
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
                                resources.files(plugin_package_name) / "../tests/scripts" / "*.sh" # noqa
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

    def list_interfaces(self, package_name="all"):
        """List the available interface[s] within [a] GeoIPS Package[s]".

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

    def list_plugins(self, interface_name, package_name="all"):
        """List the available interface[s] and their corresponding plugin names.

        Parameters
        ----------
        interface_name: str
            - The name of the interface to list. If name == "interfaces" list all
              available interfaces and their plugin names.
        package_name: str
            - The GeoIPS Package name whose scripts you want to list.
        """
        if interface_name != "plugins":
            # if the provided name != "plugins", this means we have been given a single
            # interface. Grab that interface and move on.
            interfaces_to_list = [getattr(interfaces, interface_name)]
        else:
            # List of every available interface
            interfaces_to_list = [
                getattr(interfaces, name) for name in sorted(interfaces.__all__)
            ]

        for curr_interface in interfaces_to_list:
            interface_registry, plugin_type = self._get_registry_by_interface_and_package( # noqa
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

    def _get_registry_by_interface_and_package(self, curr_interface, package_name):
        """Retrieve the correct plugin registry given interface and package name.

        Given a GeoIPS Interface and a package name, load in the correct plugin
        registry. This could be the global plugin registry which each interface has
        access to, or it could be the correct interface entry of a certain plugin
        package's "registered_plugins.json", if we are just searching through a
        single package (which occurs when -p <package_name> is given).

        Parameters
        ----------
        curr_interface: geoips.interfaces.<interface_type>
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
        if curr_interface.name in interfaces.module_based_interfaces:
            plugin_type = "module_based"
        else:
            plugin_type = "yaml_based"
        if package_name == "all":
            interface_registry = curr_interface.plugin_registry.registered_plugins[
                plugin_type
            ][curr_interface.name]
        else:
            interface_registry = json.load(
                open(resources.files(package_name) / "registered_plugins.json", "r")
            )
            if curr_interface.name in interface_registry[plugin_type]:
                interface_registry = interface_registry[plugin_type][
                    curr_interface.name
                ]
            else:
                return None, plugin_type
        return interface_registry, plugin_type

    def _print_plugins_short_format(self, curr_interface, interface_registry):
        """Print the plugins under a certain interface in alongside minimal info.

        "Short Format" includes these pieces of information:
            [GeoIPS Package, Interface, Plugin Family, Plugin Name, Relpath]

        Parameters
        ----------
        curr_interface: geoips.interfaces.<interface_type>
            - The interface we will be parsing and displaying.
        interface_registry: dict
            - The plugin registry associated with the given interface.
        """
        table_data = []
        for plugin_key in sorted(interface_registry.keys()):
            if curr_interface.name == "products":
                plugin_entry = [
                    "Not Implemented", # Package
                    curr_interface.name, # Interface
                    "list", # Family
                    plugin_key, # Plugin Name
                    "Not Implemented", # Relpath
                ]
            else:
                plugin_entry = [
                    interface_registry[plugin_key]["package"],
                    curr_interface.name,
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
                    "Family",
                    "Plugin Name",
                    "Relative Path",
                ],
                tablefmt="rounded_grid",
            )
        )