"""GeoIPS CLI "get" command.

Retrieves the appropriate plugin/interface based on the arguments provided.
"""
from colorama import Fore, Style
from glob import glob
from importlib import resources
from os.path import basename
import yaml

from geoips.commandline.cli_v2 import GeoipsCommand
from geoips import interfaces


class GeoipsGet(GeoipsCommand):
    """GeoipsGet Sub-Command for retrieving package plugins."""
    subcommand_name = "get"

    def add_arguments(self):
        self.subcommand_parser.add_argument(
            "interface_name",
            type=str.lower,
            default="algorithms",
            choices=interfaces.__all__,
            help="GeoIPS Interface to select a plugin from."
        )
        self.subcommand_parser.add_argument(
            "plugin_name",
            type=str,
            default=None,
            nargs="?",
            help="GeoIPS Plugin to select from the provided interface."
        )

    def get(self, args):
        """Retrieve the appropriate Plugin/Interface given the provided arguments.

        Retrieve the appropriate Plugin/Interface based on the arguments provided. This
        acts similar to <geoips_interface>.get_plugin(), but uses the plugin registry
        or the interface itself to get information instead.
        """
        interface_name = args.interface_name
        plugin_name = args.plugin_name

        interface = getattr(interfaces, interface_name)

        if interface.name in interfaces.module_based_interfaces:
            interface_type = "module_based"
        else:
            interface_type = "yaml_based"

        if plugin_name:
            self.get_plugin(interface, interface_type, plugin_name)
        else:
            # User just requested the interface, retrieve that now.
            self.get_interface(interface, interface_type)

    def get_interface(self, interface, interface_type):
        """CLI 'geoips get interface <interface_name>' command.

        This occurs when a user has requested a interface in the manner shown above.
        Outputs to the teriminal the following data in a dictionary format if available.

        [
            interface_name, interface_type, list_of_supported_families, docstring,
            filepath, documentation_link
        ]

        Parameters
        ----------
        interface: GeoIPS Interface Class
            - The corresponding interface to get the plugin info from
        interface_type: str
            - The type of interface provided ["module_based", "yaml_based"]
        """
        geoips_pkg_path = resources.files("geoips")
        if interface_type == "module_based":
            supported_families = list(interface.required_args.keys())
        else:
            supported_families = [
                basename(fname).split(".")[0] for fname in sorted(
                    glob(str(geoips_pkg_path / f"schema/{interface.name}/*.yaml"))
                )
            ]
        interface_path = str(
            geoips_pkg_path / f"interfaces/{interface_type}/{interface.name}.py"
        )
        interface_entry = {
            "interface": interface.name,
            "interface_type": interface_type,
            "docstring": interface.__doc__,
            "abspath": interface_path,
            "supported_families": supported_families,
        }
        self.output_dictionary_highlighted(interface_entry)

    def get_plugin(self, interface, interface_type, plugin_name):
        """CLI 'geoips get plugin <interface_name> <plugin_name>' command.

        This occurs when a user has requested a plugin in the manner shown above.
        Outputs to the teriminal the following data in a dictionary format if available.

        [
            package, interface_name, interface_type, family, call_sig/avail_overrides,
            docstring, filepath, documentation_link
        ]

        Parameters
        ----------
        interface: GeoIPS Interface Class
            - The corresponding interface to get the plugin info from
        interface_type: str
            - The type of interface provided ["module_based", "yaml_based"]
        plugin_name: str
            - The name of the plugin from the selected interface
        """


        # If plugin_name is not None, then the user has requested a plugin within
        # an interface, rather than the interface itself
        interface_registry = interface.plugin_registry.registered_plugins[
            interface_type
        ][interface.name]
        # Ensure the provided plugin exists within the interface's plugin registry
        self.ensure_plugin_exists(interface.name, interface_registry, plugin_name)
        if interface.name == "products":
            source_name, plugin_name = plugin_name.split(".", 1)
            plugin_entry = interface_registry[source_name][plugin_name]
            self.output_dictionary_highlighted(plugin_entry)
        else:
            plugin_entry = interface_registry[plugin_name]
            self.output_dictionary_highlighted(plugin_entry)

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
            raise KeyError(
                f"{plugin_name} doesn't exist within Interface {interface_name}."
            )

    def output_dictionary_highlighted(self, dict_entry):
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
        for line in yaml_text.split('\n'):
            # Color the keys in cyan and values in yellow
            if ':' in line:
                key, value = line.split(':', 1)
                formatted_line = Fore.CYAN + key + ':' + Style.RESET_ALL
                formatted_line += Fore.YELLOW + value + Style.RESET_ALL
                print(formatted_line)
            else:
                formatted_line = "\t" + Fore.YELLOW + line + Style.RESET_ALL
                print(formatted_line)
