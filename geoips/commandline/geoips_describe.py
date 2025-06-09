# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""GeoIPS CLI "describe" command.

Retrieves the appropriate family/interface/package/plugin based on the args provided.
"""

from importlib import metadata, resources, import_module

import yaml

from geoips.commandline.geoips_command import (
    CommandClassFactory,
    GeoipsCommand,
    GeoipsExecutableCommand,
)
from geoips.create_plugin_registries import format_docstring
from geoips import interfaces


class GeoipsDescribeArtifact(GeoipsExecutableCommand):
    """Command which returns information describing a GeoIPS artifact.

    Where this artifact is one of ['interface', 'plugin', 'family'.]

    This is called via `geoips describe <interface_name> <opt_args>`. Data included when
    calling this command is shown below, outputted in a yaml-based format.

    * Interface:
        * Command Signature:
            * `geoips describe <interface_name>`
        * Artifact Listing:
            * `geoips list interfaces`
        * output_info:
            * Absolute Path
            * Docstring
            * Interface Name
            * Interface Type
            * Supported Families

    * Plugin:
        * Command Signature:
            * `geoips describe <interface_name> <plugin_name>`
        * Artifact Listing:
            * `geoips list plugins <-p> <package_name>`
        * Output Info:
            * Docstring
            * Family Name
            * GeoIPS Package
            * Interface Name
            * Plugin Type
            * call_sig / source_names / Product Defaults (dependent on Plugin Type)
            * Relative Path

    * Family:
        * Command Signature:
            * `geoips describe <interface_name> family <family_name>`
        * Artifact Listing:
            * `geoips list interfaces --columns interface supported_families`
        * Output Info:
            * Docstring
            * Family Name
            * Family Path
            * Interface Name
            * Interface Type
            * Required Arguments / Schema
    """

    name = "interface"
    command_classes = []

    def add_arguments(self):
        """Add arguments to the describe-subparser for the describe Interface cmd."""
        supported_families = getattr(
            interfaces, self.name.replace("-", "_")
        ).supported_families

        self.parser.add_argument(
            "plugin_name",
            type=str,
            default=None,
            nargs="?",
            help=(
                f"If provided, prints information about the named plugin, otherwise "
                f"prints information about the {self.name} interface."
            ),
        )
        self.parser.add_argument(
            "-f",
            "--family_name",
            # "family_name",
            type=str,
            metavar="family",
            choices=supported_families,
            help=(
                "If provided, prints information about a family from the "
                f"{self.name} interface. "
                f"\n\nChoices: {', '.join(supported_families)}"
            ),
        )
        pass

    def __call__(self, args):
        """CLI 'geoips describe <interface_name>' command.

        This occurs when a user has requested a interface in the manner shown above.
        Outputs to the teriminal the following data in a dictionary format if available.

        Printed to Terminal
        -------------------
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
        if args.plugin_name and args.family_name:
            self.parser.error(
                "Invalid command: <plugin_name> and -f/--family_name are mutually "
                "exclusive."
            )
        elif args.plugin_name:
            self.describe_plugin(args)
        elif args.family_name:
            self.describe_family(args)
        else:
            self.describe_interface()

    def describe_plugin(self, args):
        """CLI 'geoips describe <interface_name> <plugin_name>' command.

        This occurs when a user has requested a plugin in the manner shown above.
        Outputs to the terminal the following data in a dictionary format if available.

        Printed to Terminal
        -------------------
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
        interface_name = self.name.replace("-", "_")
        plugin_name = args.plugin_name
        try:
            interface = getattr(interfaces, interface_name)
        except AttributeError:
            self.parser.error(
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

    def describe_family(self, args):
        """CLI 'geoips describe <interface_name> family <family_name>' command.

        This occurs when a user has requested a family in the manner shown above.
        Outputs to the terminal the following data in a dictionary format if available.

        Printed to Terminal
        -------------------
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
        interface_name = self.name.replace("-", "_")
        family_name = args.family_name
        try:
            interface = getattr(interfaces, interface_name)
        except AttributeError:
            self.parser.error(
                f"Interface: {interface_name} doesn't exist. Provide a valid interface."
            )
        interface_type = interface.interface_type
        supported_families = interface.supported_families
        if family_name not in supported_families:
            # If the family name is not one of the interface's supported family
            # members, raise an error
            err_str = f"Error: Family: `{family_name}` is not within Interface: "
            err_str += f"`{interface_name}` supported families: `{supported_families}`"
            self.parser.error(err_str)
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
            with open(family_path, "r") as fo:
                family_args_or_schema = yaml.safe_load(fo)
            if "description" in list(family_args_or_schema.keys()):
                family_args_or_schema["description"] = format_docstring(
                    family_args_or_schema["description"],
                )
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

    def describe_interface(self):
        """CLI 'geoips describe <interface_name>' command.

        This occurs when a user has requested a interface in the manner shown above.
        Outputs to the teriminal the following data in a dictionary format if available.

        Printed to Terminal
        -------------------
        yaml-based output: dict
            - Absolute Path
            - Docstring
            - Interface Name
            - Interface Type
            - Supported Families
        """
        interface_name = self.name.replace("-", "_")
        try:
            interface = getattr(interfaces, interface_name)
        except AttributeError:
            self.parser.error(
                f"Interface: {interface_name} doesn't exist. Provide a valid interface."
            )

        geoips_pkg_path = resources.files("geoips")
        interface_path = str(
            geoips_pkg_path
            / f"interfaces/{interface.interface_type}/{interface.name}.py"
        )
        interface_entry = {
            "Interface": interface.name,
            "Interface Type": interface.interface_type,
            "Docstring": format_docstring(interface.__doc__),
            "Absolute Path": interface_path,
            "Supported Families": interface.supported_families,
        }
        self._output_dictionary_highlighted(interface_entry)

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
                err_str = (
                    "Product plugins must be retrieved via `<source_name>."
                    f"<plugin_name>`. Requested {plugin_name} doesn't match that."
                )
                raise KeyError(err_str)
            source_name, plugin_name = plugin_name.split(".", 1)
            if plugin_name not in interface_registry[source_name].keys():
                raise KeyError(
                    f"{plugin_name} not found under Products {source_name} entry."
                )
        elif plugin_name not in interface_registry.keys():
            self.parser.error(
                f"{plugin_name} doesn't exist within Interface {interface_name}."
            )


class GeoipsDescribePackage(GeoipsExecutableCommand):
    """Describe Command which retrieves information about a certain GeoIPS Package.

    This is called via `geoips describe package <interface_name>`. Data included when
    calling this command is shown below, outputted in a yaml-based format.
    """

    name = "package"
    command_classes = []

    def add_arguments(self):
        """Add arguments to the describe-subparser for the describe Package Command."""
        self.parser.add_argument(
            "package_name",
            type=str.lower,
            default="geoips",
            choices=self.plugin_package_names,
            help="GeoIPS Package to retrieve.",
        )

    def __call__(self, args):
        """CLI 'geoips describe package <package_name>' command.

        This occurs when a user has requested a package in the manner shown above.
        Outputs to the teriminal the following data in a dictionary format if available.

        Printed to Terminal
        -------------------
        yaml-based output: dict
            - Docstring
            - GeoIPS Package
            - Package Path
            - Source Code
            - Version Number

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
            "Docstring": format_docstring(docstring, use_regex=False),
            "Package Path": package_path,
            "Source Code": f"{self.github_org_url}{package_name}",
            "Version Number": metadata.version(package_name),
        }
        self._output_dictionary_highlighted(package_entry)


class GeoipsDescribe(GeoipsCommand):
    """Top-Level Describe Command Class for retrieving info about GeoIPS Artifacts."""

    name = "describe"

    generated_classes = []
    for int_name in sorted(interfaces.__all__):
        generated_classes.append(
            CommandClassFactory(
                GeoipsDescribeArtifact,
                int_name.replace("_", "-"),
            ).generated_class
        )

    command_classes = generated_classes + [GeoipsDescribePackage]
