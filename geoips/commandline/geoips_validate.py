# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""GeoIPS CLI "validate" command.

Validates the appropriate plugin based on the arguments provided using the associated
interface's validation mechaninism (interface.plugin_is_valid(plugin_name)).
"""

from importlib.util import spec_from_file_location, module_from_spec
from os.path import exists
from pathlib import Path

import yaml

from geoips.commandline.geoips_command import GeoipsExecutableCommand
from geoips import interfaces


class GeoipsValidate(GeoipsExecutableCommand):
    """Validate Command for validating package plugins."""

    name = "validate"
    command_classes = []

    def add_arguments(self):
        """Add arguments to the validate-subparser fot the Validate Command."""
        self.parser.add_argument(
            "file_path",
            type=str,
            help="File path which represents a GeoIPS Plugin that we want to validate.",
        )
        self.parser.add_argument(
            "plugin_name",
            type=str,
            default=None,
            nargs="?",
            help=(
                "The name of the plugin in the file if applicable. Only useful if your "
                "file is a multi-document yaml file."
            ),
        )

    def __call__(self, args):
        """Validate the appropriate Plugin given the provided arguments.

        Validate the appropriate Plugin based on the arguments provided. This
        acts similar to <geoips_interface>.plugin_is_valid(), but uses the file_path and
        associated interface from the plugin to validate at runtime.
        """
        fpath = Path(args.file_path)
        plugin_name = args.plugin_name
        if not exists(fpath):
            self.parser.error(
                f"Provided filepath '{fpath}' doesn't exist. Provide a valid path.",
            )
        interface, plugin, plugin_name = self.get_interface_and_plugin(
            fpath, plugin_name
        )
        if interface.name == "products":
            is_valid = self.validate_sub_products(interface, fpath, plugin)
        else:
            is_valid = interface.plugin_is_valid(plugin_name)
        if not is_valid:
            # if it's not valid, report that to the user
            self.parser.error(f"Plugin '{plugin_name}' found at {fpath} is invalid.")
        else:
            # otherwise let them know they're good to go
            print(f"Plugin '{plugin_name}' found at {fpath} is valid.")

    def get_interface_and_plugin(self, fpath, plugin_name=None):
        """Retrieve the interface and plugin associated with the file path given.

        Parameters
        ----------
        fpath: str
            - The file path of the plugin requested to be validated.
        plugin_name: str, default=None
            - If provided and the filepath is a .yaml file, assume this is a
              multi-document yaml file (such as a workflow plugin), and attempt to
              find the plugin matching 'plugin_name' in that document.

        Returns
        -------
        interface: GeoIPS Interface Class
            - The interface associated with the provided plugin.
        plugin: Python Module or Yaml Dictionary
            - The plugin "definition" associated with the file path provided.
        plugin_name: str
            - The name of the plugin
        """
        if fpath.suffix == ".py":
            # module-based plugin
            interface_type = "module_based"
            plugin = self._load_module_from_file(fpath)
        elif fpath.suffix == ".yaml":
            # yaml-based plugin
            interface_type = "yaml_based"
        else:
            self.parser.error(
                "Only '.py' and '.yaml' files are accepted at this time. Try again."
            )
        try:
            # if the module / yaml plugin is missing either interface or name, it's
            # invalid and we need to report the error appropriately
            if interface_type == "module_based":
                interface_name = plugin.interface
                plugin_name = plugin.name
            else:
                # If plugin_name already exists, assume this is a multi-document yaml
                # file and attempt to find the correct plugin within that file
                if plugin_name:
                    docs = yaml.safe_load_all(open(fpath, "r"))
                    plugin = None
                    for doc in docs:
                        if doc["name"] == plugin_name:
                            plugin = doc
                            break
                    # No matching plugin could be found. Raise an error
                    if not plugin:
                        self.parser.error(
                            f"Error: No plugin under name '{plugin_name}' could be "
                            f"in the multi-document yaml plugin at {fpath}."
                        )
                else:
                    with open(fpath, "r") as fo:
                        plugin = yaml.safe_load(fo)
                interface_name = plugin["interface"]
                plugin_name = plugin["name"]
        except AttributeError or KeyError:
            # Report such error.
            err_str = f"Plugin found at {fpath} doesn't have 'interface' and/or "
            err_str += "'name' attribute[s]. This plugin is invalid."
            self.parser.error(err_str)
        # get the correct geoips interface associated with the plugin
        interface = getattr(interfaces, interface_name)
        return interface, plugin, plugin_name

    def _load_module_from_file(self, file_path, module_name=None):
        """Load in a given python module provided a file_path and an optional name."""
        if module_name is None:
            # Generate a unique module name if not provided
            module_name = "module_from_"
            module_name += (
                str(file_path).replace("/", "_").replace(".", "_").replace("\\", "_")
            )

        spec = spec_from_file_location(module_name, file_path)
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def validate_sub_products(self, interface, fpath, plugin):
        """Validate each sub-product plugin found within a products yaml definition.

        If the corresponding interface was found to be a "products" interface, validate
        each sub-product plugin found within the provided yaml products plugin.

        Parameters
        ----------
        interface: GeoIPS Interface Class
            - GeoIPS Products Interface used for validation
        fpath: str
            - The file path of the products plugin to be validated
        plugin: dict
            - Dictionary representing the Products' yaml file provided.

        Returns
        -------
        bool:
            - True or False, where True means that every sub-plugin is valid and False
              means that at least a single sub-plugin was invalid.
        """
        try:
            product_list = plugin["spec"]["products"]
        except KeyError:
            err_str = f"Plugin '{plugin['name']} found at {fpath} is invalid. "
            err_str += "Missing either 'spec' or 'spec['products']' key."
            print(err_str)
            return False

        for subplg in product_list:
            if not interface.plugin_is_valid(subplg["source_names"][0], subplg["name"]):
                return False
        return True
