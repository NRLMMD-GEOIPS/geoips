"""GeoIPS CLI "validate" command.

Retrieves the appropriate plugin/interface based on the arguments provided.
"""
from importlib.util import (
    spec_from_file_location,
    module_from_spec,
)
import yaml

from geoips.commandline.commandline_interface import GeoipsCommand
from geoips import interfaces


class GeoipsValidate(GeoipsCommand):
    """GeoipsValidate Sub-Command for validating package plugins."""
    subcommand_name = "validate"
    subcommand_classes = []

    def add_arguments(self):
        self.subcommand_parser.add_argument(
            "file_path",
            type=str,
            help="File path which represents a GeoIPS Plugin that we want to validate."
        )

    def validate(self, args):
        """Validate the appropriate Plugin given the provided arguments.

        Validate the appropriate Plugin based on the arguments provided. This
        acts similar to <geoips_interface>.plugin_is_valid(), but uses the file_path and
        associated interface from the plugin to validate at runtime.
        """
        fpath = args.file_path
        if ".py" == fpath[-3:]:
            # module-based plugin
            interface_type = "module_based"
            plugin = self.load_module_from_file(fpath)
        elif ".yaml" == fpath[-5:]:
            # yaml-based plugin
            interface_type = "yaml_based"
            plugin = yaml.safe_load(open(fpath, "r"))
        else:
            self.subcommand_parser.error(
                f"Only '.py' and '.yaml' files are accepted at this time. Try again."
            )
        try:
            # if the module / yaml plugin is missing either interface or name, it's
            # invalid and we need to report the error appropriately
            if interface_type == "module_based":
                interface_name = plugin.interface
                plugin_name = plugin.name
            else:
                interface_name = plugin["interface"]
                plugin_name = plugin["name"]
        except AttributeError or KeyError:
            # Report such error.
            err_str = f"Plugin found at {fpath} doesn't have 'interface' and/or "
            err_str += "'name' attribute[s]. This plugin is invalid."
            self.subcommand_parser.error(
                err_str
            )
        # get the correct interface and validate the plugin based on its name
        interface = getattr(interfaces, interface_name)
        is_valid = interface.plugin_is_valid(plugin_name)
        if not is_valid:
            # if it's not valid, report that to the user
            self.subcommand_parser.error(
                f"Plugin '{plugin_name}' found at {fpath} is invalid."
            )
        else:
            # otherwise let them know they're good to go
            print(f"Plugin '{plugin_name}' found at {fpath} is valid.")

    def load_module_from_file(self, file_path, module_name=None):
        """Load in a given python module provied a file_path and an optional name."""
        if module_name is None:
            # Generate a unique module name if not provided
            module_name = 'module_from_' + file_path.replace('/', '_').replace('.', '_')

        spec = spec_from_file_location(module_name, file_path)
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        return module