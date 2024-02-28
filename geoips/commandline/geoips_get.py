"""GeoIPS CLI "Get" command.

Retrieves the appropriate plugin/interface based on the arguments provided.
"""


import inspect
from tabulate import tabulate
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
            help="GeoIPS Plugin to select from the provided interface."
        )

    def get(self, args):
        """Retrieve the appropriate Plugin/Interface given the provided arguments.

        Retrieve the appropriate Plugin/Interface based on the arguments provided. This
        acts similar to <geoips_interface>.get_plugin().
        """
        interface_name = args.interface_name
        plugin_name = args.plugin_name
        if interface_name in interfaces.module_based_interfaces:
            interface_type = "module_based"
        else:
            interface_type = "yaml_based"

        interface = getattr(interfaces, interface_name)

        if plugin_name:
            # If plugin_name is not None, then the user has requested a plugin within
            # an interface, rather than the interface itself
            interface_registry = getattr(
                interfaces,
                interface_name,
            ).plugin_registry.registered_plugins[interface_type][interface_name]
            if plugin_name in interface_registry.keys():
                print(
                    interface.get_plugin(plugin_name)
                )
            else:
                raise KeyError(
                    f"{plugin_name} doesn't exist within Interface {interface_name}."
                )
        else:
            # User just requested the interface, retrieve that now.
            interface_data = [
                interface.name, # interface name
                interface.__doc__, # docstring
                len(interface.get_plugins()), # num plugins
            ]
            print(
                tabulate(
                    interface_data,
                    headers=[
                        "Interface Name",
                        "Docstring",
                        "Num Plugins",
                    ]
                )
            )
