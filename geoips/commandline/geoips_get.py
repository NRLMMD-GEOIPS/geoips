"""GeoIPS CLI "get" command.

Retrieves the appropriate family/interface/package/plugin based on the args provided.
"""

from importlib import resources, import_module
import yaml

from geoips.commandline.geoips_command import GeoipsCommand, GeoipsExecutableCommand
from geoips import interfaces


class GeoipsGetFamily(GeoipsExecutableCommand):
    """GeoipsGetFamily Class which implements retrieving GeoIPS Families.

    This is called via `geoips get family <interface_name> <family_name>`. Data included
    when calling this command is shown below, outputted in a yaml-based format.
    """

    subcommand_name = "family"
    subcommand_classes = []

    def add_arguments(self):
        """Add arguments to the get-subparser for the Get Family Command."""
        self.subcommand_parser.add_argument(
            "interface_name",
            type=str.lower,
            default="algorithms",
            choices=interfaces.__all__,
            help="GeoIPS Interface to retrieve.",
        )
        self.subcommand_parser.add_argument(
            "family_name",
            type=str,
            help="GeoIPS Plugin to select from the provided interface.",
        )

    def __call__(self, args):
        """CLI 'geoips get family <interface_name> <family_name>' command.

        This occurs when a user has requested a family in the manner shown above.
        Outputs to the teriminal the following data in a dictionary format if available.

        Data Output
        -----------
        yaml-based output: dict
            - Docstring
            - Family Name
            - Family Path
            - Interface Name
            - Interface Type
            - Required Arguments / Schema

        Parameters
        ----------
        args: Argparse Namespace()
            - The list argument namespace to parse through
        """
        interface_name = args.interface_name
        family_name = args.family_name
        try:
            interface = getattr(interfaces, interface_name)
        except AttributeError:
            self.subcommand_parser.error(
                f"Interface: {interface_name} doesn't exist. Provide a valid interface."
            )
        interface_type = interface.interface_type
        supported_families = interface.supported_families
        if family_name not in supported_families:
            # If the family name is not one of the interface's supported family
            # members, raise an error
            err_str = f"Error: Family: `{family_name}` is not within Interface: "
            err_str += f"`{interface_name}` supported families: `{supported_families}`"
            self.subcommand_parser.error(err_str)
        if interface_type == "module_based":
            docstring = "Not Implemented."
            family_path = str(
                resources.files("geoips")
                / f"interfaces/{interface_type}/{interface_name}.py"
            )
            family_args_or_schema = interface.required_args[family_name]
        else:
            family_path = str(
                resources.files("geoips")
                / f"schema/{interface_name}/{family_name}.yaml"
            )
            family_args_or_schema = yaml.safe_load(open(family_path, "r"))
            if "description" in list(family_args_or_schema.keys()):
                docstring = family_args_or_schema["description"]
            else:
                docstring = "Not Implemented."
        family_entry = {
            "Interface Name": interface_name,
            "Interface Type": interface_type,
            "Family Name": family_name,
            "Required Args / Schema": family_args_or_schema,
            "Docstring": docstring,
            "Family Path": family_path,
        }
        self._output_dictionary_highlighted(family_entry)


class GeoipsGetInterface(GeoipsExecutableCommand):
    """GeoipsGetInterface Class which implements retrieving GeoIPS Interfaces.

    This is called via `geoips get interface <interface_name>`. Data included when
    calling this command is shown below, outputted in a yaml-based format.
    """

    subcommand_name = "interface"
    subcommand_classes = []

    def add_arguments(self):
        """Add arguments to the get-subparser for the Get Interface Command."""
        self.subcommand_parser.add_argument(
            "interface_name",
            type=str.lower,
            default="algorithms",
            choices=interfaces.__all__,
            help="GeoIPS Interface to retrieve.",
        )

    def __call__(self, args):
        """CLI 'geoips get interface <interface_name>' command.

        This occurs when a user has requested a interface in the manner shown above.
        Outputs to the teriminal the following data in a dictionary format if available.

        Data Output
        -----------
        yaml-based output: dict
            - Absolute Path
            - Docstring
            - Interface Name
            - Interface Type
            - Supported Families

        Parameters
        ----------
        args: Argparse Namespace()
            - The list argument namespace to parse through
        """
        interface_name = args.interface_name
        try:
            interface = getattr(interfaces, interface_name)
        except AttributeError:
            self.subcommand_parser.error(
                f"Interface: {interface_name} doesn't exist. Provide a valid interface."
            )

        geoips_pkg_path = resources.files("geoips")
        interface_path = str(
            geoips_pkg_path
            / f"interfaces/{interface.interface_type}/{interface.name}.py"
        )
        interface_entry = {
            "interface": interface.name,
            "interface_type": interface.interface_type,
            "docstring": interface.__doc__,
            "abspath": interface_path,
            "supported_families": interface.supported_families,
        }
        self._output_dictionary_highlighted(interface_entry)


class GeoipsGetPackage(GeoipsExecutableCommand):
    """GeoipsGetPackage Class which implements retrieving GeoIPS Packages.

    This is called via `geoips get package <interface_name>`. Data included when
    calling this command is shown below, outputted in a yaml-based format.
    """

    subcommand_name = "package"
    subcommand_classes = []

    def add_arguments(self):
        """Add arguments to the get-subparser for the Get Package Command."""
        self.subcommand_parser.add_argument(
            "package_name",
            type=str.lower,
            default="geoips",
            choices=self.plugin_packages,
            help="GeoIPS Package to retrieve.",
        )

    def __call__(self, args):
        """CLI 'geoips get package <package_name>' command.

        This occurs when a user has requested a package in the manner shown above.
        Outputs to the teriminal the following data in a dictionary format if available.

        Data Output
        -----------
        yaml-based output: dict
            - Docstring
            - Documentation Link
            - GeoIPS Package
            - Package Path

        Parameters
        ----------
        args: Argparse Namespace()
            - The list argument namespace to parse through
        """
        package_name = args.package_name
        package_path = str(resources.files(package_name))

        docstring = import_module(package_name).__doc__
        package_entry = {
            "GeoIPS Package": package_name,
            "Docstring": docstring,
            "Package Path": package_path,
            "Documentation Link": f"{self.nrl_url}{package_name}",
        }
        self._output_dictionary_highlighted(package_entry)


class GeoipsGetPlugin(GeoipsExecutableCommand):
    """GeoipsGetPlugin Class which implements retrieving GeoIPS Plugins.

    This is called via `geoips get plugin <interface_name> <plugin_name>`. Data included
    when calling this command is shown below, outputted in a yaml-based format.
    """

    subcommand_name = "plugin"
    subcommand_classes = []

    def add_arguments(self):
        """Add arguments to the get-subparser for the Get Plugin Command."""
        self.subcommand_parser.add_argument(
            "interface_name",
            type=str.lower,
            default="algorithms",
            choices=interfaces.__all__,
            help="GeoIPS Interface to retrieve.",
        )
        self.subcommand_parser.add_argument(
            "plugin_name",
            type=str,
            default=None,
            nargs="?",
            help="GeoIPS Plugin to select from the provided interface.",
        )

    def __call__(self, args):
        """CLI 'geoips get plugin <interface_name> <plugin_name>' command.

        This occurs when a user has requested a plugin in the manner shown above.
        Outputs to the teriminal the following data in a dictionary format if available.

        Data Output
        -----------
        yaml-based output: dict
            - Docstring
            - Family Name
            - GeoIPS Package
            - Interface Name
            - Plugin Type
            - call_sig / source_names / Product Defaults (dependent on Plugin Type)
            - Relative Path

        Parameters
        ----------
        args: Argparse Namespace()
            - The list argument namespace to parse through
        """
        interface_name = args.interface_name
        plugin_name = args.plugin_name
        try:
            interface = getattr(interfaces, interface_name)
        except AttributeError:
            self.subcommand_parser.error(
                f"Interface: {interface_name} doesn't exist. Provide a valid interface."
            )
        # If plugin_name is not None, then the user has requested a plugin within
        # an interface, rather than the interface itself
        interface_registry = interface.plugin_registry.registered_plugins[
            interface.interface_type
        ][interface.name]
        # Ensure the provided plugin exists within the interface's plugin registry
        self.ensure_plugin_exists(interface.name, interface_registry, plugin_name)
        if interface.name == "products":
            source_name, plugin_name = plugin_name.split(".", 1)
            plugin_entry = interface_registry[source_name][plugin_name]
            self._output_dictionary_highlighted(plugin_entry)
        else:
            plugin_entry = interface_registry[plugin_name]
            self._output_dictionary_highlighted(plugin_entry)

    def ensure_plugin_exists(self, interface_name, interface_registry, plugin_name):
        """Ensure that the given plugin exists within an interface's plugin registry.

        If the plugin is not found within the interface's registry, raise a KeyError,
        otherwise, just return.

        Parameters
        ----------
        interface_name: str
            - The name of the selected GeoIPS Interface
        interface_registry: dict
            - The plugin registry for the selected GeoIPS Interface
        plugin_name: str
            - The name of the plugin from the selected interface
        """
        if interface_name == "products":
            if "." not in plugin_name:
                err_str = "Product plugins must be retrieved via `<source_name>."
                err_str += f"<plugin_name>`. Requested {plugin_name} doesn't match"
                err_str += "that."
                raise KeyError(err_str)
            source_name, plugin_name = plugin_name.split(".", 1)
            if plugin_name not in interface_registry[source_name].keys():
                raise KeyError(
                    f"{plugin_name} not found under Products {source_name} entry."
                )
        elif plugin_name not in interface_registry.keys():
            self.subcommand_parser.error(
                f"{plugin_name} doesn't exist within Interface {interface_name}."
            )


class GeoipsGet(GeoipsCommand):
    """GeoipsGet Sub-Command for retrieving package plugins."""

    subcommand_name = "get"
    subcommand_classes = [
        GeoipsGetFamily,
        GeoipsGetInterface,
        GeoipsGetPackage,
        GeoipsGetPlugin,
    ]
