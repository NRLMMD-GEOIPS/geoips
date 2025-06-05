# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""GeoIPS CLI "list" command.

Lists the appropriate interfaces/packages/plugins based on the arguments provided.
"""

from glob import glob
from importlib import metadata, resources, import_module
import json
from os import listdir
from os.path import basename, exists
import sys

import numpy as np
from tabulate import tabulate

from geoips.commandline.ancillary_info.test_data import test_dataset_dict
from geoips.commandline.geoips_command import (
    CommandClassFactory,
    GeoipsCommand,
    GeoipsExecutableCommand,
)
from geoips.geoips_utils import is_editable, get_remote_file_size
from geoips import interfaces


class GeoipsListRegistries(GeoipsExecutableCommand):
    """List Command for listing out plugin registries from installed plugin packages.

    This command is used to easily expose what plugin packages have plugin registries
    created.
    """

    name = "registries"
    command_classes = []

    def add_arguments(self):
        """Add arguments to the list-subparser for the List Registries Command."""
        self.parser.add_argument(
            "-n",
            "--namespace",
            type=str,
            default="geoips.plugin_packages",
            help=(
                "The namespace of plugin packages to list plugin registries for. "
                "If not specified, this defaults to 'geoips.plugin_packages'."
            ),
        )
        self.parser.add_argument(
            "-r",
            "--relpath",
            default=False,
            action="store_true",
            help=(
                "Whether or not you want the paths for the plugin registry files to be "
                "displayed as relative paths. Default is false, which means the paths "
                "will be shown as absolute."
            ),
        )

    def __call__(self, args):
        """List all plugin registries under 'namespace' held under <package_name>.

        Printed to Terminal
        -------------------
        out_array: 2D Array of Strings
            - GeoIPS Package
            - .json registry path
            - .yaml registry path

        Parameters
        ----------
        args: Namespace()
            - The list argument namespace to parse through
        """
        namespace = args.namespace
        relpath = args.relpath
        package_name = args.package_name
        default_headers = {
            "package": "GeoIPS Package",
            "json": "JSON Path",
            "yaml": "YAML Path",
        }
        headers = self._get_headers_by_command(args, default_headers)
        registry_list = []
        packages = metadata.entry_points(group=namespace)

        if len(packages) == 0:
            self.parser.error(
                f"Error: no plugin packages exist under namespace '{namespace}'."
            )

        for pkg in metadata.entry_points(group=namespace):
            pkg_path = resources.files(pkg.value)
            json_path = str(pkg_path / "registered_plugins.json")
            yaml_path = str(pkg_path / "registered_plugins.yaml")

            json_path = json_path if exists(json_path) else "missing"
            yaml_path = yaml_path if exists(yaml_path) else "missing"

            json_path = basename(json_path) if relpath else json_path
            yaml_path = basename(yaml_path) if relpath else yaml_path

            reg_entry = [pkg.value, json_path, yaml_path]

            if package_name != "all" and pkg.value == package_name:
                registry_list.append(reg_entry)
                break
            elif package_name == "all":
                registry_list.append(reg_entry)
            else:
                continue

        if len(registry_list) == 0:
            self.parser.error(
                f"Error: plugin package '{package_name}' could not be found in "
                f"namespace '{namespace}'."
            )

        print("-" * len("Plugin Package Registries"))
        print("Plugin Package Registries")
        print("-" * len("Plugin Package Registries"))
        print(
            tabulate(
                sorted(registry_list),
                headers=headers.values(),
                tablefmt="rounded_grid",
                maxcolwidths=self.terminal_width // len(headers),
            )
        )


class GeoipsListSourceNames(GeoipsExecutableCommand):
    """List Command for listing out source_names from available reader plugins.

    This command is used to easily expose what source_names are supported by each
    reader. If a reader module is missing the source_name attribute, then that will be
    notified in the CLI output.
    """

    name = "source-names"
    command_classes = []

    def add_arguments(self):
        """Add arguments to the list-subparser for the List Source Names Command."""
        pass

    def __call__(self, args):
        """List all source-names in reader plugins held under <package_name>.

        Printed to Terminal
        -------------------
        out_array: 2D Array of Strings
            - GeoIPS Package
            - Source Names
            - Reader Name

        Parameters
        ----------
        args: Namespace()
            - The list argument namespace to parse through
        """
        package_name = args.package_name
        default_headers = {
            "source_name": "Source Name",
            "reader_names": "Reader Names",
        }
        interface_registry = self._get_registry_by_interface_and_package(
            interfaces.readers, package_name
        )
        if interface_registry is None:
            print(
                f"\nPlugin Package '{package_name}' has no reader plugins and "
                "therefore no implemented source_names."
            )
            return
        headers = self._get_headers_by_command(args, default_headers)
        src_name_mapping = self.match_readers_with_source_name(interface_registry)
        src_name_info = []
        for src_name, rdrs in src_name_mapping.items():
            src_name_entry = []
            for header in list(headers.keys()):
                if header == "source_name":
                    src_name_entry.append(src_name)
                elif header == "reader_names":
                    src_name_entry.append(list(rdrs))
            src_name_info.append(src_name_entry)
        if package_name == "all":
            package_name = "All GeoIPS Plugin Packages"
        print("-" * len(f"'{package_name}' Reader Source Names"))
        print(f"'{package_name}' Reader Source Names")
        print("-" * len(f"'{package_name}' Reader Source Names"))
        print(
            tabulate(
                sorted(src_name_info),
                headers=headers.values(),
                tablefmt="rounded_grid",
                maxcolwidths=self.terminal_width // len(headers),
            )
        )

    def match_readers_with_source_name(self, registry):
        """Assemble a dictionary of <source_name>:[readers] for tabular listing.

        Match source_names found in the registry to readers which support that
        source_name. Each key in the dictionary will be a unique source_name with values
        that are the names of readers which support that source_name.

        Parameters
        ----------
        registry: dict
            - The readers portion of all GeoIPS plugin packages' plugin registries or
              a single package's plugin registry.

        Returns
        -------
        src_name_mapping: dict
            - A dictionary mapping of source_name:[readers] which links readers to a
              unique source_name which they support.
        """
        src_name_mapping = {}
        for rdr_name in registry:
            src_names = registry[rdr_name]["source_names"]
            for src_name in src_names:
                if src_name not in src_name_mapping:
                    src_name_mapping[src_name] = set([rdr_name])
                else:
                    src_name_mapping[src_name].add(rdr_name)
        return src_name_mapping


class GeoipsListUnitTests(GeoipsExecutableCommand):
    """List Command for listing out available unit tests.

    Called via `geoips list unit-tests`. Outputs the following in a tabular format.
    """

    name = "unit-tests"
    command_classes = []

    def add_arguments(self):
        """Add arguments to the list-subparser for the List Unit Tests Command."""
        pass

    def __call__(self, args):
        """List all of the available unit-tests held under <package_name>.

        Printed to Terminal
        -------------------
        out_array: 2D Array of Strings
            - Data Host
            - Dataset Name

        Parameters
        ----------
        args: Namespace()
            - The list argument namespace to parse through
        """
        package_name = args.package_name
        if package_name == "all":
            package_names = self.plugin_package_names
        else:
            package_names = [package_name]
        default_headers = {
            "package": "GeoIPS Package",
            "unit_test_dir": "Unit Test Directory",
            "unit_test_name": "Unit Test Name",
        }
        headers = self._get_headers_by_command(args, default_headers)
        for pkg_name in package_names:
            unit_test_info = []
            if not is_editable(pkg_name):
                # Package is installed in non-editable mode and we will not be able to
                # access unit tests. Raise a runtime error reporting this.
                print(
                    f"Error: Package '{pkg_name}' is installed in non-editable mode and"
                    " we are not able to access it's unit tests. For this command to "
                    f"work, please install '{pkg_name}' in editable mode via: "
                    f"'pip install -e <path_to_{pkg_name}>'",
                    file=sys.stderr,
                )
                # We use a print to sys.stderr so monkeypatch unit tests can catch this
                # output
                raise RuntimeError(
                    f"Package '{pkg_name}' isn't installed in editable mode."
                )
            unit_test_dir = str(resources.files(pkg_name) / "../tests/unit_tests")
            try:
                listdir(unit_test_dir)
            except FileNotFoundError:
                # I'm not sure why len(package_names) == 1 would indicate that the
                # unit-tests folder does not exist.  Instead, check if the unit-tests
                # folder exists to see if it exists.
                # if len(package_names) == 1:
                if not exists(unit_test_dir):
                    err_str = f"No unit test directory found under {pkg_name}. "
                    err_str += "Please create a tests/unit_tests folder for that "
                    err_str += "package if you want to continue."
                    self.parser.error(err_str)
                else:
                    print(f"package_names: {package_names}")
                    print(f"No unit tests found in '{pkg_name}', continuing.")
                    continue
            for subdir_name in listdir(unit_test_dir):
                for unit_test in sorted(
                    glob(f"{unit_test_dir}/{subdir_name}/test*.py")
                ):  # noqa
                    unit_test_entry = []
                    for header in list(headers.keys()):
                        if header == "package":
                            unit_test_entry.append(pkg_name)
                        elif header == "unit_test_dir":
                            unit_test_entry.append(subdir_name)
                        elif header == "unit_test_name":
                            unit_test_entry.append(basename(unit_test))
                    unit_test_info.append(unit_test_entry)
            print("-" * len(f"'{pkg_name}' Unit Tests"))
            print(f"'{pkg_name}' Unit Tests")
            print("-" * len(f"'{pkg_name}' Unit Tests"))
            print(
                tabulate(
                    unit_test_info,
                    headers=headers.values(),
                    tablefmt="rounded_grid",
                    # maxcolwidths=self.terminal_width // len(headers),
                )
            )


class GeoipsListTestDatasets(GeoipsExecutableCommand):
    """List Command for listing off available test-datasets used by GeoIPS.

    Called via `geoips list test-datasets`. Outputs the following in a tabular format.
    """

    name = "test-datasets"
    command_classes = []

    def add_arguments(self):
        """Add arguments to the list-subparser for the List Test Datasets Command.

        Since this command requires no additional arguments, we pass for the time being.
        """
        pass

    def __call__(self, args):
        """List all of the test datasets used by GeoIPS.

        Printed to Terminal
        -------------------
        out_array: 2D Array of Strings
            - Data Host
            - Dataset Name

        Parameters
        ----------
        args: Namespace()
            - The list argument namespace to parse through
        """
        if args.package_name != "all":
            self.parser.error("Error: '-p' flag is not supported for this command")
        dataset_info = []
        default_headers = {
            "data_host": "Data Host",
            "dataset_name": "Dataset Name",
            "size": "Size",
        }
        headers = self._get_headers_by_command(args, default_headers)
        file_sizes = []
        for test_dataset_name in list(test_dataset_dict.keys()):
            dataset_entry = []
            for header in list(headers.keys()):
                if header == "data_host":
                    dataset_entry.append("io.cira.colostate.edu")
                elif header == "dataset_name":
                    dataset_entry.append(test_dataset_name)
                elif header == "size":
                    # Add a human readable string of the size of the file
                    dataset_entry.append(
                        get_remote_file_size(test_dataset_dict[test_dataset_name])
                    )
                    # Track the file size in bytes of each file
                    file_sizes.append(
                        get_remote_file_size(
                            test_dataset_dict[test_dataset_name], in_bytes=True
                        )
                    )
            dataset_info.append(dataset_entry)
        if "size" in headers:
            # Sort in order of largest file to smallest file
            # Need to convert to np arrays to get argsort to work
            dataset_info = np.array(dataset_info)
            file_sizes = np.array(file_sizes)
            sorted_idxs = np.argsort(file_sizes * -1)
            # Multiply by -1 to get the array sorted by largest to smallest
            dataset_info = dataset_info[sorted_idxs]

        print("-" * len("Available Test Datasets"))
        print("Available Test Datasets")
        print("-" * len("Available Test Datasets"))
        print(
            tabulate(
                dataset_info,
                headers=headers.values(),
                tablefmt="rounded_grid",
                maxcolwidths=self.terminal_width // len(headers),
            )
        )


class GeoipsListInterfaces(GeoipsExecutableCommand):
    """List Command for listing interfaces and interface-specific plugins.

    Will either list information about available GeoIPS interfaces (done via
    `geoips list interfaces`), or list information about implemented interface-specific
    plugins implemented in all, or a certain package (done via
    'geoips list interfaces -i <-p> <package_name>').

    Called via `geoips list interfaces`. Outputs the following data in a tabular format.
    """

    name = "interfaces"
    command_classes = []

    def add_arguments(self):
        """Add arguments to the list-subparser for the List Interfaces Command."""
        self.parser.add_argument(
            "--implemented",
            "-i",
            default=False,
            action="store_true",
            help=str(
                "Flag to list what's implemented in each package, "
                + "rather than what's available."
            ),
        )

    def __call__(self, args):
        """List the available interface[s] within [a] GeoIPS Package[s]".

        Printed to Terminal (either available or implemented)
        -----------------------------------------------------
        available_out_array: 2D Array of Strings
            - Absolute Path
            - Docstring
            - GeoIPS Package
            - Interface Type
            - Interface Name
            - Supported Families
        implemented_out_array: 2D Array of Strings
            - GeoIPS Package
            - Interface Type
            - Interface Name

        Parameters
        ----------
        args: Argparse Namespace()
            - The Argument Namespace for GeoipsListInterfaces Command
        """
        package_name = args.package_name
        # Flag representing whether or not we want to list what's implemented or
        # what's available.
        implemented = args.implemented
        if package_name != "all" or (implemented and package_name):
            # If you're listing a certain package, implemented is implied. If it's
            # 'all' packages, make sure implemented as added if we are going to list in
            # that fasion.
            self.list_implemented_interfaces(package_name, args)
        else:
            # Otherwise just list off available interfaces.
            self.list_available_interfaces(args)

    def list_available_interfaces(self, args):
        """List the available interface[s] within [a] GeoIPS Package[s]".

        Printed to Terminal
        -------------------
        out_array: 2D Array of Strings
            - Absolute Path
            - Docstring
            - GeoIPS Package
            - Interface Type
            - Interface Name
            - Supported Families

        Parameters
        ----------
        args: argparse Argument Namespace
            - The arguments provided to a certain list command
        """
        interface_data = []
        default_headers = {
            "package": "GeoIPS Package",
            "plugin_type": "Interface Type",
            "interface": "Interface Name",
            "supported_families": "Supported Families",
            "docstring": "Docstring",
            "abspath": "Absolute Path",
        }
        headers = self._get_headers_by_command(args, default_headers)
        for interface_name in interfaces.__all__:
            interface = getattr(interfaces, interface_name)
            interface_entry = []
            for header in list(headers.keys()):
                if header == "package":
                    interface_entry.append("geoips")
                elif header == "plugin_type":
                    interface_entry.append(interface.interface_type)
                elif header == "interface":
                    interface_entry.append(interface_name)
                elif header == "supported_families":
                    interface_entry.append(",\n".join(interface.supported_families))
                elif header == "docstring":
                    interface_entry.append(interface.__doc__.split("\n")[0])
                elif header == "abspath":
                    interface_entry.append(
                        str(
                            resources.files("geoips")
                            / f"interfaces/{interface.interface_type}/{interface.name}.py"  # noqa
                        ),
                    )
            interface_data.append(interface_entry)

        print("-" * len("GeoIPS Interfaces"))
        print("GeoIPS Interfaces")
        print("-" * len("GeoIPS Interfaces"))
        print(
            tabulate(
                interface_data,
                headers=headers.values(),
                tablefmt="rounded_grid",
                maxcolwidths=self.terminal_width // len(headers),
            )
        )

    def list_implemented_interfaces(self, package_name, args):
        """List the implemented interface[s] within [a] GeoIPS Package[s].

        Ie. search through all, or an individual package and list off what has been
        implemented in such package[s].

        Printed to Terminal
        -------------------
        out_array: 2D Array of Strings
            - GeoIPS Package
            - Interface Type
            - Interface Name

        Parameters
        ----------
        package_name: str
            - The GeoIPS Package name whose scripts you want to list.
        args: argparse Argument Namespace
            - The arguments provided to a certain list command
        """
        default_headers = {
            "package": "GeoIPS Package",
            "plugin_type": "Interface Type",
            "interface": "Interface Name",
        }
        headers = self._get_headers_by_command(args, default_headers)
        for plugin_package_name, pkg_path in zip(
            self.plugin_package_names, self.plugin_package_paths
        ):

            if package_name == "all" or package_name == plugin_package_name:
                with open(
                    f"{pkg_path}/{plugin_package_name}/registered_plugins.json", "r"
                ) as fo:
                    pkg_registry = json.load(fo)
            else:
                continue
            interface_data = []
            for interface_type in pkg_registry.keys():
                for interface_name in pkg_registry[interface_type].keys():
                    interface_entry = []
                    for header in list(headers.keys()):
                        if header == "package":
                            interface_entry.append(plugin_package_name)
                        elif header == "plugin_type":
                            interface_entry.append(interface_type)
                        elif header == "interface":
                            interface_entry.append(interface_name)
                    interface_data.append(interface_entry)
            print("-" * len(f"{plugin_package_name.title()} Interfaces"))
            print(f"{plugin_package_name.title()} Interfaces")
            print("-" * len(f"{plugin_package_name.title()} Interfaces"))
            if len(interface_data) == 0:
                print(f"Package '{plugin_package_name.title()}' has no interfaces.")
            else:
                print(
                    tabulate(
                        interface_data,
                        headers=headers.values(),
                        tablefmt="rounded_grid",
                        maxcolwidths=self.terminal_width // len(headers),
                    )
                )


class GeoipsListPackages(GeoipsExecutableCommand):
    """List Command for listing off installed GeoIPS Packages.

    Called via `geoips list packages`. Outputs the following data in a tabular format.
    """

    name = "packages"
    command_classes = []

    def add_arguments(self):
        """No arguments for the list-subparser for the List Packages Command."""
        pass

    def __call__(self, args):
        """List all of the available GeoIPS Packages.

        Only installed packages will be listed. Ie, if geoips_clavrx, or another
        suitable package exists, but is not installed, it will not be listed.

        Printed to Terminal
        -------------------
        out_array: 2D Array of Strings
            - Docstring
            - GeoIPS Package
            - Package Path
            - Version Number

        Parameters
        ----------
        args: Argparse Namespace()
            - The Argument Namespace for GeoipsListPackages Command
        """
        if args.package_name != "all":
            # 'all' is the default for package name. We don't support the -p argument
            # for this command so we need to raise an error
            self.parser.error("Error: '-p' flag is not supported for this command")
        pkg_data = []
        default_headers = {
            "package": "GeoIPS Package",
            "docstring": "Docstring",
            "package_path": "Package Path",
            "version": "Version Number",
        }
        headers = self._get_headers_by_command(args, default_headers)
        pkg_name_requested = False
        for package_name, package_path in zip(
            self.plugin_package_names, self.plugin_package_paths
        ):

            pkg_entry = []
            docstring = import_module(package_name).__doc__
            for header in headers:
                if header == "package":
                    pkg_name_requested = True
                    pkg_entry.append(package_name)
                elif header == "docstring":
                    pkg_entry.append(str(docstring))
                elif header == "package_path":
                    pkg_entry.append(package_path)
                elif header == "version":
                    pkg_entry.append(metadata.version(package_name))
            pkg_data.append(pkg_entry)

        if pkg_name_requested:
            # If package name is in the list of headers, make sure we don't wrap that
            # name. This will cause failed tests and this is a workaround that ensures
            # the package name is not broken into multiple lines / words.
            colwidths = [None] + (len(headers) - 1) * [
                self.terminal_width // (len(headers))
            ]
        else:
            # Otherwise just keep it as normal.
            colwidths = self.terminal_width // len(headers)

        print("-" * len("GeoIPS Packages"))
        print("GeoIPS Packages")
        print("-" * len("GeoIPS Packages"))
        print(
            tabulate(
                pkg_data,
                headers=headers.values(),
                tablefmt="rounded_grid",
                maxcolwidths=colwidths,
            )
        )


class GeoipsListPlugins(GeoipsExecutableCommand):
    """List Command for listing off plugins in all, or a certain GeoIPS Package.

    Called via `geoips list plugins`. Outputs the following data in a tabular format.
    """

    name = "plugins"
    command_classes = []

    def add_arguments(self):
        """Add arguments to the list-subparser for the List Plugins Command."""
        pass

    def __call__(self, args):
        """List the available interface[s] and their corresponding plugin names.

        Printed to Terminal
        -------------------
        out_array: 2D Array of Strings
            - Family Name
            - GeoIPS Package
            - Interface Name
            - Interface Type
            - Plugin Name
            - Relative Path

        Parameters
        ----------
        args: Argparse Namespace()
            - The list argument namespace to parse through
        """
        package_name = args.package_name
        # List of every available interface
        interfaces_to_list = [
            getattr(interfaces, name) for name in sorted(interfaces.__all__)
        ]

        plugin_found = False
        for curr_interface in interfaces_to_list:
            interface_registry = self._get_registry_by_interface_and_package(
                curr_interface, package_name
            )
            # Interface Registry can be None if we are looking through a specific
            # package whose registry doesn't contain that certain interface.
            if interface_registry is None:
                continue
            else:
                plugin_found = True
            print("-" * len(curr_interface.name))
            print(curr_interface.name)
            print("-" * len(curr_interface.name))
            self._print_plugins(curr_interface, interface_registry, args)
        if not plugin_found:
            print(f"Plugin package '{package_name.title()}' has no plugins.")


class GeoipsListSingleInterface(GeoipsExecutableCommand):
    """List Command for listing plugins of a single interface."""

    name = "interface"
    command_classes = []

    def add_arguments(self):
        """Instantiate the valid arguments that are supported for the list command.

        Currently the "geoips list interface" command supports this format:
            - geoips list interface <interface_name> -p <package_name>
        Where:
            - <interface_name> is any of the GeoIPS Interfaces' Name
            - <package_name> is any GeoIPS package that is installed and recognized by
              the GeoIPS Library
        """
        pass

    def __call__(self, args):
        """List all elements of the selected list option.

        Selected list option is args.interface_name, where interface_name can be any of:
            - any geoips.interface

        Where any of those options can be GeoIPS Package specific or from any package.

        Printed to Terminal
        -------------------
        out_array: 2D array of Strings
            - Family Name
            - GeoIPS Package
            - Interface Name
            - Interface Type
            - Plugin Name
            - Relative Path

        Parameters
        ----------
        args: Namespace()
            - The list argument namespace to parse through
        """
        interface_name = self.name.replace("-", "_")
        package_name = args.package_name
        try:
            interface = getattr(interfaces, interface_name)
        except AttributeError:
            self.parser.error(
                f"Interface: {interface_name} doesn't exist. Provide a valid interface."
            )
        interface_registry = self._get_registry_by_interface_and_package(
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
            self._print_plugins(interface, interface_registry, args)


class GeoipsListScripts(GeoipsExecutableCommand):
    """List Command for listing test scripts from all, or a certain GeoIPS Package.

    Called via `geoips list scripts`. Outputs the following data in a tabular format.
    """

    name = "scripts"
    command_classes = []

    def add_arguments(self):
        """Add arguments to the list-subparser for the List Scripts Command."""
        pass

    def __call__(self, args):
        """List all of the available scripts held under <package_name>.

        Printed to Terminal
        -------------------
        out_array: 2D Array of Strings
            - GeoIPS Package
            - Script Name

        Parameters
        ----------
        args: Namespace()
            - The list argument namespace to parse through
        """
        package_name = args.package_name
        # columns = args.columns
        if package_name == "all":
            # list scripts found throughout all packages.
            plugin_package_names = self.plugin_package_names
        else:
            # list scripts from a certain package.
            plugin_package_names = [package_name]
        default_headers = {"package": "GeoIPS Package", "filename": "Filename"}
        headers = self._get_headers_by_command(args, default_headers)
        for plugin_package_name in plugin_package_names:
            if not is_editable(plugin_package_name):
                # Package is installed in non-editable mode and we will not be able to
                # access unit tests. Raise a runtime error reporting this.
                print(
                    f"Error: Package '{plugin_package_name}' is installed in "
                    "non-editable mode and we are not able to access it's unit tests.\n"
                    f"For this command to work, please install '{plugin_package_name}' "
                    "in editable mode via:\n'pip install -e "
                    f"<path_to_{plugin_package_name}>'",
                    file=sys.stderr,
                )
                # We use a print to sys.stderr so monkeypatch unit tests can catch this
                # output
                raise RuntimeError(
                    f"Package '{plugin_package_name}' isn't installed in editable mode."
                )
            script_names = sorted(
                [
                    [plugin_package_name, basename(fpath)]
                    for fpath in glob(
                        str(
                            resources.files(plugin_package_name)
                            / "../tests/scripts"
                            / "*.sh"
                        )
                    )
                ]
            )
            if headers != default_headers:
                for script_idx in range(len(script_names)):
                    if list(headers.keys())[0] == "package":
                        script_names[script_idx] = [script_names[script_idx][0]]
                    else:
                        script_names[script_idx] = [script_names[script_idx][1]]
            print("-" * len(f"{plugin_package_name.title()} Available Scripts"))
            print(f"{plugin_package_name.title()} Available Scripts")
            print("-" * len(f"{plugin_package_name.title()} Available Scripts"))
            if len(script_names) == 0:
                print(f"Package '{plugin_package_name.title()}' has no scripts.")
            else:
                print(
                    tabulate(
                        script_names,
                        headers=headers.values(),
                        tablefmt="rounded_grid",
                        maxcolwidths=self.terminal_width // len(headers),
                    )
                )


class GeoipsList(GeoipsCommand):
    """Top-Level List Command for listing off GeoIPS Artifacts."""

    name = "list"
    generated_classes = []
    for int_name in sorted(interfaces.__all__):
        generated_classes.append(
            CommandClassFactory(
                GeoipsListSingleInterface,
                int_name.replace("_", "-"),
            ).generated_class
        )

    command_classes = generated_classes + [
        GeoipsListInterfaces,
        GeoipsListPackages,
        GeoipsListPlugins,
        GeoipsListRegistries,
        GeoipsListScripts,
        GeoipsListSourceNames,
        GeoipsListTestDatasets,
        GeoipsListUnitTests,
    ]
