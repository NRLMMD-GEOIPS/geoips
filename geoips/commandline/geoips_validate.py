# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""GeoIPS CLI "validate" command.

Validates the appropriate plugin based on the arguments provided using the associated
interface's validation mechanism (interface.plugin_is_valid(plugin_name)).
"""

from importlib.util import spec_from_file_location, module_from_spec
from os.path import exists
from pathlib import Path

import geoips_yaml_utils as yaml
from pydantic import ValidationError

from geoips.commandline.geoips_command import GeoipsExecutableCommand
from geoips.config.plugins import discover_config_plugins
from geoips.config.schema import GeoSettings
from geoips.config.yaml_loader import find_project_config
from geoips import interfaces


def _resolve_config_path(file_arg: Path | None) -> Path | None:
    """Resolve the config file path from an optional argument.

    If *file_arg* is provided, returns it. Otherwise searches standard
    locations via ``geoips.config.yaml_loader.find_project_config``.

    Parameters
    ----------
    file_arg : pathlib.Path or None
        User-supplied file path, or ``None`` to auto-search.

    Returns
    -------
    pathlib.Path or None
        Resolved path, or ``None`` if no config file was found.
    """
    if file_arg is not None:
        return file_arg

    found = find_project_config()
    return Path(found) if found else None


def _validate_config_file(file_path: Path) -> list[str]:
    """Validate a GeoIPS YAML configuration file.

    Checks YAML syntax, validates core settings against the GeoIPS
    configuration model, and validates each ``geoips.plugins.<pkg>`` section
    against its registered plugin model. Unknown top-level settings and
    unknown plugin names are reported as warnings, since they are silently
    ignored at load time.

    Parameters
    ----------
    file_path : pathlib.Path
        Path to the ``.geoips.yaml`` file to validate.

    Returns
    -------
    tuple[list[str], list[str]]
        A ``(errors, warnings)`` pair of human-readable messages. An empty
        *errors* list means the file is valid.
    """
    errors: list[str] = []
    warnings: list[str] = []

    try:
        with open(file_path, "r") as fh:
            data = yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        return [f"YAML syntax error: {exc}"], warnings
    except OSError as exc:
        return [f"Cannot read file: {exc}"], warnings

    if not isinstance(data, dict):
        return ["File must contain a YAML mapping (dictionary)."], warnings

    geoips_data = data.get("geoips")
    if geoips_data is None:
        return ["Missing top-level 'geoips' key."], warnings

    if not isinstance(geoips_data, dict):
        return ["The 'geoips' key must contain a mapping (dictionary)."], warnings

    known_keys = set(GeoSettings.model_fields) | {"plugins"}
    for key in geoips_data:
        if key not in known_keys:
            warnings.append(f"geoips.{key}: unknown setting (ignored)")

    core_data = {k: v for k, v in geoips_data.items() if k != "plugins"}
    try:
        GeoSettings.model_validate(core_data)
    except ValidationError as exc:
        for err in exc.errors():
            loc = ".".join(str(p) for p in err["loc"])
            errors.append(f"geoips.{loc}: {err['msg']}")

    errors.extend(_validate_plugins_section(geoips_data.get("plugins"), warnings))

    return errors, warnings


def _validate_plugins_section(plugins_data, warnings: list[str]) -> list[str]:
    """Validate the ``geoips.plugins`` mapping against registered plugins.

    Parameters
    ----------
    plugins_data : Any
        The value of ``geoips.plugins`` from the config file (or ``None``).
    warnings : list[str]
        List appended to in-place with warnings for unknown plugins.

    Returns
    -------
    list[str]
        Error messages for invalid plugin sections.
    """
    if plugins_data is None:
        return []
    if not isinstance(plugins_data, dict):
        return ["geoips.plugins: must be a mapping (dictionary)."]

    errors: list[str] = []
    registered = discover_config_plugins()
    for pkg, pkg_data in plugins_data.items():
        plugin = registered.get(pkg)
        if plugin is None:
            warnings.append(f"geoips.plugins.{pkg}: unknown plugin (ignored)")
            continue
        if not isinstance(pkg_data, dict):
            errors.append(f"geoips.plugins.{pkg}: must be a mapping (dictionary).")
            continue
        try:
            plugin.settings_model.model_validate(pkg_data)
        except ValidationError as exc:
            for err in exc.errors():
                loc = ".".join(str(p) for p in err["loc"])
                errors.append(f"geoips.plugins.{pkg}.{loc}: {err['msg']}")
    return errors


class GeoipsValidateConfig(GeoipsExecutableCommand):
    """Validate a GeoIPS .geoips.yaml configuration file.

    Checks YAML syntax, verifies the structure against the GeoIPS
    configuration schema, and reports all errors found.
    """

    name = "config"
    command_classes = []

    def add_arguments(self):
        """Add arguments to the validate-subparser for the config command."""
        self.parser.add_argument(
            "-f",
            "--file",
            type=Path,
            default=None,
            help="Path to the config file to validate. If not given, "
            "searches standard locations.",
        )
        self.parser.add_argument(
            "-q",
            "--quiet",
            action="store_true",
            default=False,
            help="Only set the exit code; produce no output.",
        )

    def __call__(self, args):
        """Run ``geoips validate config``.

        Parameters
        ----------
        args : Namespace
            Parsed command-line arguments.
        """
        file_path = _resolve_config_path(args.file)

        if file_path is None:
            self.parser.error(
                "No config file found. Specify --file or place a .geoips.yaml "
                "in the current directory."
            )

        errors, warnings = _validate_config_file(file_path)

        if warnings and not args.quiet:
            for warning in warnings:
                print(f"  warning: {warning}")

        if errors:
            if not args.quiet:
                print(f"Config file '{file_path}' is invalid:\n")
                for err in errors:
                    print(f"  {err}")
            self.parser.error("Validation failed.")
        else:
            if not args.quiet:
                print(f"Config file '{file_path}' is valid.")


class GeoipsValidate(GeoipsExecutableCommand):
    """Validate Command for validating package plugins."""

    name = "validate"
    command_classes = [GeoipsValidateConfig]

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
        elif interface.interface_type == "yaml_based":
            is_valid = interface.plugin_is_valid(plugin_name)
        else:
            is_valid = interface.plugin_is_valid(
                interface._plugin_module_to_obj(plugin_name, plugin)
            )
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
        except (AttributeError, KeyError):
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
