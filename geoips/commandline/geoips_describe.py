# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Implement CLI commands for describing GeoIPS interfaces and plugin packages."""

from importlib import import_module, metadata, resources

from pluginify.create_plugin_registries import format_docstring
import geoips_yaml_utils as yaml

from geoips.commandline.geoips_command import (
    CommandClassFactory,
    GeoipsCommand,
    GeoipsExecutableCommand,
)
from geoips import interfaces

_DISPLAY_ARG_MAP = {
    "fnames": "filenames",
    "output_fnames": "output_filenames",
}


def _translate_display_args(family_args_or_schema):
    """Replace legacy arg names with display-friendly equivalents.

    Parameters
    ----------
    family_args_or_schema : list or dict
        Required args list (class-based interface) or YAML schema dict.

    Returns
    -------
    list or dict
        The same structure with ``fnames`` → ``filenames`` and
        ``output_fnames`` → ``output_filenames`` in list elements /
        dict keys.
    """
    if isinstance(family_args_or_schema, list):
        return [_DISPLAY_ARG_MAP.get(a, a) for a in family_args_or_schema]
    if isinstance(family_args_or_schema, dict):
        return {_DISPLAY_ARG_MAP.get(k, k): v for k, v in family_args_or_schema.items()}
    return family_args_or_schema


class GeoipsDescribeArtifact(GeoipsExecutableCommand):
    """Describe an interface or one of its registered plugins or families."""

    name = "interface"
    command_classes = []

    def _format_instructions(self, instructions):
        """Insert this generated command's interface name into shared instructions."""
        formatted = instructions.copy()
        for field in ("help", "description", "usage"):
            if field in formatted:
                formatted[field] = formatted[field].format(interface=self.name)
        if "output_info" in formatted:
            formatted["output_info"] = [
                item.format(interface=self.name) for item in formatted["output_info"]
            ]
        return formatted

    def add_arguments(self):
        """Add plugin and family arguments to a generated interface command."""
        self.parser.add_argument(
            "plugin_name",
            type=str,
            default=None,
            nargs="?",
            metavar="PLUGIN",
            help="GeoIPS plugin to describe.",
        )
        self.parser.add_argument(
            "family_name",
            type=str,
            default=None,
            nargs="?",
            metavar="FAMILY",
            choices=getattr(interfaces, self.name.replace("-", "_")).supported_families,
            help="GeoIPS family to describe.",
        )

    def __call__(self, args):
        """Describe the interface, plugin, or family selected by ``args``.

        Parameters
        ----------
        args : argparse.Namespace
            Parsed arguments for the generated interface command.
        """
        if (
            args.plugin_name
            and args.plugin_name != "family"
            and args.plugin_name != "fam"
        ):
            self.describe_plugin(args)
        elif (
            args.plugin_name == "family" or args.plugin_name == "fam"
        ) and args.family_name:
            self.describe_family(args)
        elif args.plugin_name is None and args.family_name is None:
            self.describe_interface()
        else:
            self.parser.error(
                f"A family name is required after '{args.plugin_name}'. Run "
                f"'geoips describe {self.name} -h' for usage."
            )

    def describe_plugin(self, args):
        """Describe a registered plugin from this command's interface.

        Parameters
        ----------
        args : argparse.Namespace
            Parsed arguments containing the requested plugin name.
        """
        interface_name = self.name.replace("-", "_")
        plugin_name = args.plugin_name
        try:
            interface = getattr(interfaces, interface_name)
        except AttributeError:
            self.parser.error(
                f"Interface '{self.name}' does not exist. Use 'geoips list interfaces' "
                "to find valid interface names."
            )
        # If plugin_name is not None, then the user has requested a plugin within
        # an interface, rather than the interface itself
        interface_registry = interface.plugin_registry.registered_plugins[
            interface.interface_type
        ][interface.name]
        # Ensure the provided plugin exists within the interface's plugin registry
        self.ensure_plugin_exists(interface.name, interface_registry, plugin_name)
        if interface.name == "products":
            source_name, plugin_name = plugin_name.split(":", 1)
            plugin_entry = interface_registry[source_name][plugin_name]
            self._output_dictionary_highlighted(plugin_entry)
        else:
            plugin_entry = interface_registry[plugin_name]
            self._output_dictionary_highlighted(plugin_entry)

    def describe_family(self, args):
        """Describe a supported family from this command's interface.

        Parameters
        ----------
        args : argparse.Namespace
            Parsed arguments containing the requested family name.
        """
        interface_name = self.name.replace("-", "_")
        family_name = args.family_name
        try:
            interface = getattr(interfaces, interface_name)
        except AttributeError:
            self.parser.error(
                f"Interface '{self.name}' does not exist. Use 'geoips list interfaces' "
                "to find valid interface names."
            )
        interface_type = interface.interface_type
        supported_families = interface.supported_families
        if family_name not in supported_families:
            self.parser.error(
                f"Family '{family_name}' is not supported by interface '{self.name}'. "
                f"Choose from: {', '.join(supported_families)}."
            )
        if interface_type == "class_based":
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
        family_args_or_schema = _translate_display_args(family_args_or_schema)
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
        """Describe this command's GeoIPS interface."""
        interface_name = self.name.replace("-", "_")
        try:
            interface = getattr(interfaces, interface_name)
        except AttributeError:
            self.parser.error(
                f"Interface '{self.name}' does not exist. Use 'geoips list interfaces' "
                "to find valid interface names."
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
        """Ensure that a plugin is registered with the selected interface.

        Parameters
        ----------
        interface_name : str
            Name of the selected GeoIPS interface.
        interface_registry : dict
            Registry entries for the selected interface.
        plugin_name : str
            Name of the requested plugin.
        """
        if interface_name == "products":
            if ":" not in plugin_name:
                err_str = (
                    "Product plugins must be specified as SOURCE_NAME:PLUGIN. "
                    f"Received '{plugin_name}'."
                )
                raise KeyError(err_str)
            source_name, plugin_name = plugin_name.split(":", 1)
            if plugin_name not in interface_registry[source_name].keys():
                raise KeyError(
                    f"Plugin '{plugin_name}' was not found for source '{source_name}' "
                    "in the products interface."
                )
        elif plugin_name not in interface_registry.keys():
            self.parser.error(
                f"Plugin '{plugin_name}' is not registered with interface "
                f"'{self.name}'."
            )


class GeoipsDescribePackage(GeoipsExecutableCommand):
    """Describe an installed GeoIPS plugin package."""

    name = "package"
    command_classes = []

    def add_arguments(self):
        """Add the plugin package argument to the package command."""
        self.parser.add_argument(
            "package_name",
            type=str.lower,
            metavar="PACKAGE",
            choices=self.plugin_package_names,
            help="Installed GeoIPS plugin package to describe.",
        )

    def __call__(self, args):
        """Describe the installed plugin package selected by ``args``.

        Parameters
        ----------
        args : argparse.Namespace
            Parsed arguments containing the requested plugin package name.
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
    """Provide commands for describing GeoIPS interfaces and plugin packages."""

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
