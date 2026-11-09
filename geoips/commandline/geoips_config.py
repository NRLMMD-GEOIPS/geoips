# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""GeoIPS CLI "config" command.

Various configuration-based commands for setting up your geoips environment.
"""

import logging
import os
import pathlib
from importlib import metadata

import yaml
from pydantic import ValidationError

from geoips.commandline.geoips_command import GeoipsCommand, GeoipsExecutableCommand
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


def _resolve_config_path(file_arg: pathlib.Path | None) -> pathlib.Path | None:
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
    return pathlib.Path(found) if found else None


def _validate_config_file(file_path: pathlib.Path) -> list[str]:
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


class GeoipsConfigCreate(GeoipsExecutableCommand):
    """Generate a .geoips.yaml config file from environment variables.

    Scans ``GEOIPS_*`` and unprefixed environment variables and writes
    them as a structured YAML configuration file. Interactively prompts
    for key variables (GEOIPS_OUTDIRS, GEOIPS_TESTDATA_DIR,
    GEOIPS_PACKAGES_DIR) that are not set in the environment.
    """

    name = "create"
    command_classes = []

    _KEYS_TO_PROMPT: list[str] = [
        "GEOIPS_OUTDIRS",
        "GEOIPS_TESTDATA_DIR",
        "GEOIPS_PACKAGES_DIR",
    ]

    def add_arguments(self):
        """Add arguments to the config-subparser for the create command."""
        self.parser.add_argument(
            "-o",
            "--output",
            type=pathlib.Path,
            default=pathlib.Path(".geoips.yaml"),
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
        """Run ``geoips config create``.

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


class GeoipsConfigValidate(GeoipsExecutableCommand):
    """Validate a GeoIPS .geoips.yaml configuration file.

    Checks YAML syntax, verifies the structure against the GeoIPS
    configuration schema, and reports all errors found.
    """

    name = "validate"
    command_classes = []

    def add_arguments(self):
        """Add arguments to the config-subparser for the validate command."""
        self.parser.add_argument(
            "-f",
            "--file",
            type=pathlib.Path,
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
        """Run ``geoips config validate``.

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


class GeoipsConfig(GeoipsCommand):
    """Config top-level command for configuring your GeoIPS environment."""

    name = "config"
    command_classes = [
        GeoipsConfigCreate,
        GeoipsConfigValidate,
    ]
