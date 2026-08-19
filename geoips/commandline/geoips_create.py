# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""GeoIPS CLI "create" command.

Creates configuration, registry, and sector image files.
"""

from importlib import metadata
import logging
import os
from os.path import exists, join
from pathlib import Path

# from pytest import main as invoke_pytest
from pluginify.commandline_typer import configure_logging
from pluginify.plugin_registry import PluginRegistry
import yaml

from geoips.commandline.geoips_command import (
    GeoipsCommand,
    GeoipsExecutableCommand,
)
from geoips.config.config import GeoIPSConfig, _cast_env_value
from geoips.config.plugins import (
    CONFIG_PLUGIN_GROUP,
    build_plugin_env_map,
    cast_plugin_target,
    discover_config_plugins,
    field_comment,
    full_model_defaults,
    is_nested_model,
)
from geoips.config.schema import GEOIPS_ENV_MAP, GeoSettings
from geoips.config.yaml_loader import find_project_config
from geoips.errors import PluginError
from geoips.filenames.base_paths import PATHS
from geoips.interfaces import sectors

LOG = logging.getLogger(__name__)


def _combined_env_map() -> dict[str, str]:
    """Return the core env map merged with all plugin-contributed env vars."""
    return {**GEOIPS_ENV_MAP, **build_plugin_env_map()}


def _collect_env_overrides() -> dict[str, str]:
    """Collect GeoIPS configuration values from environment variables.

    Iterates the combined core + plugin env map and returns a mapping of
    environment variable name to value for every variable that is set.

    Returns
    -------
    dict[str, str]
        Mapping of environment variable name to raw string environment values.
    """
    overrides: dict[str, str] = {}
    for env_var in _combined_env_map():
        raw = os.environ.get(env_var)
        if raw is not None:
            overrides[env_var] = raw
    return overrides


def _prompt_for_missing(
    overrides: dict[str, str], keys_to_prompt: list[str]  # NOQA
) -> dict[str, str]:
    """Interactively prompt the user for missing configuration values.

    Parameters
    ----------
    overrides : dict[str, str]
        Existing overrides keyed by environment variable name.
    keys_to_prompt : list[str]
        Environment variable names to prompt for if absent from *overrides*.

    Returns
    -------
    dict[str, str]
        New overrides from user input, keyed by environment variable name.
    """
    prompted: dict[str, str] = {}
    defaults = {
        "GEOIPS_OUTDIRS": os.path.join(
            os.environ.get("HOME", os.path.expanduser("~")), "geoips_outdirs"
        ),
        "GEOIPS_TESTDATA_DIR": os.path.join(
            os.environ.get("HOME", os.path.expanduser("~")), "geoips_testdata"
        ),
        "GEOIPS_PACKAGES_DIR": os.path.join(
            os.environ.get("HOME", os.path.expanduser("~")), "geoips_packages"
        ),
    }

    for key in keys_to_prompt:
        env_val = os.environ.get(key)
        if env_val is not None:
            continue

        default = defaults.get(key, "")
        value = input(f"\n  {key} [default: {default}]: ").strip()
        prompted[key] = value if value else default

    return prompted


def _build_nested_config(overrides: dict[str, str]) -> dict:
    """Convert flat env-var overrides into a nested YAML-ready dictionary.

    Uses the combined core + plugin env map to translate environment variable
    names into dot-separated field paths, then nests them. Plugin values
    (``plugins.<pkg>.<field>``) are cast against their plugin model's field
    type; core values use the core caster.

    Parameters
    ----------
    overrides : dict[str, str]
        Mapping of environment variable names to raw string values.

    Returns
    -------
    dict
        Nested dictionary suitable for ``yaml.dump``.
    """
    combined = _combined_env_map()

    result: dict = {}
    for env_var, raw_value in overrides.items():
        field_path = combined.get(env_var, "")
        if not field_path:
            continue
        if field_path.startswith("plugins."):
            cast = cast_plugin_target(field_path, raw_value)
        else:
            cast = _cast_env_value(raw_value, field_path)
        parts = field_path.split(".")
        node = result
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = cast
    return result


def _deep_merge(base: dict, override: dict) -> None:
    """Recursively merge *override* into *base* in-place.

    Nested dictionaries are merged; scalar values are replaced.

    Parameters
    ----------
    base : dict
        Target dictionary updated in-place.
    override : dict
        Source dictionary whose values take precedence.
    """
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


def _indent_lines(text: str, indent: int) -> list[str]:
    """Indent every non-empty line of *text* by *indent* spaces."""
    pad = " " * indent
    return [pad + line if line else line for line in text.rstrip("\n").split("\n")]


def _format_scalar(key: str, value) -> str:
    """Render ``key: value`` for a scalar/list using flow style (single line)."""
    dumped = yaml.safe_dump({key: value}, default_flow_style=True, sort_keys=False)
    return dumped.strip()[1:-1]


def _dump_annotated(values: dict, model_cls, indent: int) -> list[str]:
    """Render a plugin's values as YAML lines with per-field default comments.

    Parameters
    ----------
    values : dict
        The plugin field values to render (in declared order).
    model_cls : type[pydantic.BaseModel]
        The plugin settings model, used for comments and nested structure.
    indent : int
        Number of leading spaces for this level.

    Returns
    -------
    list[str]
        YAML lines, each scalar annotated with a ``# default: ...`` comment.
    """
    pad = " " * indent
    lines: list[str] = []
    fields = model_cls.model_fields
    for key, value in values.items():
        field_info = fields.get(key)
        nested_cls = is_nested_model(field_info.annotation) if field_info else None
        comment = field_comment(model_cls, key) if field_info else ""
        if isinstance(value, dict) and nested_cls is not None:
            header = f"{pad}{key}:"
            if comment:
                header += f"  # {comment}"
            lines.append(header)
            lines += _dump_annotated(value, nested_cls, indent + 2)
            continue
        line = f"{pad}{_format_scalar(key, value)}"
        if comment:
            line += f"  # {comment}"
        lines.append(line)
    return lines


def _plugin_dist_names() -> dict[str, str | None]:
    """Return a mapping of config-plugin name to its distribution name."""
    names: dict[str, str | None] = {}
    for entry in metadata.entry_points(group=CONFIG_PLUGIN_GROUP):
        dist = getattr(entry, "dist", None)
        names[entry.name] = dist.name if dist is not None else None
    return names


def _render_config(core_nested: dict, plugin_values: dict, plugins: dict) -> str:
    """Render the full ``geoips:`` YAML document with annotated plugin blocks.

    Parameters
    ----------
    core_nested : dict
        Core (non-plugin) settings to render under ``geoips:``.
    plugin_values : dict
        Mapping of plugin name to its field-value dict.
    plugins : dict
        Registered ``ConfigPlugin`` objects keyed by name (for models/comments).

    Returns
    -------
    str
        The complete YAML file content.
    """
    lines = ["geoips:"]
    if core_nested:
        lines += _dump_annotated(core_nested, GeoSettings, 2)

    if plugin_values:
        dist_names = _plugin_dist_names()
        lines.append("  plugins:")
        for name in sorted(plugin_values):
            dist = dist_names.get(name)
            header = f"    # Plugin: {name}" + (f" ({dist})" if dist else "")
            lines.append(header)
            lines.append(f"    {name}:")
            plugin = plugins.get(name)
            if plugin is not None:
                lines += _dump_annotated(plugin_values[name], plugin.settings_model, 6)
            else:
                sub = yaml.dump(
                    plugin_values[name], default_flow_style=False, sort_keys=False
                )
                lines += _indent_lines(sub, 6)

    return "\n".join(lines) + "\n"


class GeoipsCreateConfig(GeoipsExecutableCommand):
    """Generate a .geoips.yaml config file from environment variables.

    Scans ``GEOIPS_*`` and unprefixed environment variables and writes
    them as a structured YAML configuration file. Interactively prompts
    for key variables (GEOIPS_OUTDIRS, GEOIPS_TESTDATA_DIR,
    GEOIPS_PACKAGES_DIR) that are not set in the environment.
    """

    name = "config"
    command_classes = []

    _KEYS_TO_PROMPT: list[str] = [
        "GEOIPS_OUTDIRS",
        "GEOIPS_TESTDATA_DIR",
        "GEOIPS_PACKAGES_DIR",
    ]

    def add_arguments(self):
        """Add arguments to the create-subparser for the config command."""
        self.parser.add_argument(
            "-o",
            "--output",
            type=Path,
            default=Path(".geoips.yaml"),
            help="Output path for the generated config file.",
        )
        self.parser.add_argument(
            "-f",
            "--force",
            action="store_true",
            default=False,
            help="Overwrite the output file if it already exists.",
        )
        self.parser.add_argument(
            "-a",
            "--all",
            action="store_true",
            default=False,
            help="Include all default settings, not just env overrides.",
        )
        self.parser.add_argument(
            "--no-prompt",
            action="store_true",
            default=False,
            help="Skip interactive prompts; generate only from environment variables.",
        )

    def __call__(self, args):
        """Run ``geoips create config``.

        Parameters
        ----------
        args : Namespace
            Parsed command-line arguments.
        """
        overrides = _collect_env_overrides()

        if not args.no_prompt:
            prompted = _prompt_for_missing(overrides, self._KEYS_TO_PROMPT)
            overrides.update(prompted)

        if not overrides and not args.all:
            print(
                "No GEOIPS environment variables found. "
                "Use --all to generate a complete config file with defaults, "
                "or remove --no-prompt for interactive setup."
            )
            return

        nested = _build_nested_config(overrides)
        plugin_values = nested.pop("plugins", {})
        core_nested = nested

        plugins = discover_config_plugins()

        if args.all:
            # Dump the fully-resolved config (auto-derived paths filled in) so
            # the generated file is complete and valid on reload — raw model
            # defaults contain nulls (e.g. cache_dir) that break reloading.
            resolved = GeoIPSConfig().model_dump()
            _deep_merge(resolved, core_nested)
            core_nested = resolved

            full_plugins: dict = {}
            for name, plugin in plugins.items():
                plugin_defaults = full_model_defaults(plugin.settings_model)
                _deep_merge(plugin_defaults, plugin_values.get(name, {}))
                full_plugins[name] = plugin_defaults
            plugin_values = full_plugins

        content = _render_config(core_nested, plugin_values, plugins)

        output_path = args.output.resolve()
        if output_path.exists() and not args.force:
            self.parser.error(
                f"File '{output_path}' already exists. Use --force to overwrite."
            )

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as fh:
            fh.write(content)

        num_env = len([k for k in overrides if os.environ.get(k)])
        num_prompted = len(overrides) - num_env

        parts = []
        if num_env:
            parts.append(f"{num_env} environment variable{'s' if num_env != 1 else ''}")
        if num_prompted:
            parts.append(
                f"{num_prompted} prompted value{'s' if num_prompted != 1 else ''}"
            )
        source = " and ".join(parts) if parts else "default settings"

        print(f"Generated {output_path} from {source}.")


class GeoipsCreateRegistries(GeoipsExecutableCommand):
    """Command class for creating plugin registries for plugin packages."""

    name = "registries"
    command_classes = []

    def add_arguments(self):
        """Add arguments to the create-subparser for the registries Command."""
        self.parser.add_argument(
            "-s",
            "--save-type",
            default="json",
            type=str,
            choices=["json", "yaml"],
            help=(
                "The file format to save the registry as. Defaults to 'json', which is "
                "what's used by GeoIPS under the hood. For human readable output, you "
                "can provide the optional argument '-s yaml'."
            ),
        )

    def __call__(self, args):
        """Run the `geoips create registries -n <namespace> -s <save_type> -p <packages>` command.  # NOQA

        Parameters
        ----------
        args: Namespace()
            - The argument namespace to parse through
        """
        packages = args.packages
        namespace = args.namespace
        save_type = args.save_type
        # This is needed to ensure that we capture the logs from pluginify
        configure_logging()
        plugin_registry = PluginRegistry(namespace)
        plugin_registry.create_registries(packages, save_type)


class GeoipsCreateSector(GeoipsExecutableCommand):
    """Command for creating a sector image based on the provided sector name.

    This used to be ran via 'create_sector_image', however we are trying to consolidate
    all independent console scripts to be used via the CLI. When this command is called
    an image of the provided sector will be created so we can view whether or not it
    matches the region of the globe we'd like to study.
    """

    name = "sector"
    command_classes = []

    def add_arguments(self):
        """Instantiate the arguments that are supported for the create sector command.

        Currently the "geoips create sector" command supports this format:
            - geoips create sector <sector_name> --outdir <output_directory_path>
        Where:
            - <sector_name> is the name of any GeoIPS Sector Plugin that has an entry in
              any package's plugin registry.
            - --outdir is the full path to the directory in which you'd like to create
              the sector image.
        """
        self.parser.add_argument(
            "sector_name",
            type=str,
            help="Name of the sector plugin to create an image from.",
        )
        self.parser.add_argument(
            "--outdir",
            "-o",
            type=str,
            default=PATHS["GEOIPS_OUTDIRS"],
            help="The output directory to create your sector image in.",
        )
        self.parser.add_argument(
            "--overlay",
            default=False,
            action="store_true",
            help=(
                "Overlay this sector on the global_cylindrical grid. Useful for testing"
                "small sectors, where their domain might be difficult to interpret in "
                "a geospatial context."
            ),
        )
        self.parser.add_argument(
            "--gridlines",
            "-g",
            default=False,
            action="store_true",
            help="Add a latitude / longitude gridline overlay to your sector.",
        )
        self.parser.add_argument(
            "--labels",
            "-l",
            default=["left", "bottom"],
            choices=["left", "right", "top", "bottom"],
            nargs="*",
            help=(
                "A list of strings which set where gridline labels will be set on the "
                "sector. Specify no values to disable labels."
            ),
        )

    def __call__(self, args):
        """Create the provided sector image based off the arguments provided.

        This will retrieve the selected sector plugin from any GeoIPS Plugin package,
        then create an image of that sector. This is a good way to quickly test whether
        or not your sector plugin covers the area you expected with the correct
        resolution.

        Parameters
        ----------
        args: Argparse Namespace()
            - The list argument namespace to parse through
        """
        sector_name = args.sector_name
        outdir = args.outdir
        overlay = args.overlay
        gridlines = args.gridlines
        labels = args.labels
        noborder = False if len(labels) else True

        # If the path to outdir doesn't already exist, make that path
        if not exists(outdir):
            os.makedirs(outdir)
        # Create an image for the requested sector, including just the map and white
        # background.
        fname = join(outdir, f"{sector_name}.png")
        try:
            if "non_existent" in sector_name:
                # This occurs for a unit test that we are just checking the error output
                # for. No need to rebuild the plugin registry, which can be specified by
                # using rebuild_registries=False
                rebuild_registries = False
            else:
                # Otherwise, assume this is a new sector that is being developed, and
                # automate plugin registry creation if it does not already exist as an
                # entry in the registry.
                rebuild_registries = True
            sect = sectors.get_plugin(
                sector_name, rebuild_registries=rebuild_registries
            )
        except PluginError:
            raise self.parser.error(
                f"Sector '{sector_name}' is not a valid plugin.\nPlease use a plugin "
                "found under 'geoips list interface sectors' or create a new plugin "
                f"named '{sector_name}' and run 'pluginify create'."
            )
        print(f"Creating {fname}.")
        sect.create_test_plot(
            fname,
            overlay=overlay,
            gridlines=gridlines,
            gridline_labels=labels,
            noborder=noborder,
        )


class GeoipsCreate(GeoipsCommand):
    """Top-Level create command for instantiating sub-command creation routines."""

    name = "create"

    command_classes = [
        GeoipsCreateConfig,
        GeoipsCreateSector,
        GeoipsCreateRegistries,
    ]
