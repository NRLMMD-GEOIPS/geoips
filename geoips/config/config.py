# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""GeoIPS configuration loader.

Provides :class:`GeoIPSConfig` — an immutable, layered configuration
container that merges defaults, project YAML overrides, and environment
variable overrides with a well-defined priority order.
"""

from __future__ import annotations

import logging
import os
import socket
import warnings
from typing import Any

import platformdirs

from geoips.config.schema import GEOIPS_ENV_MAP, GeoSettings
from geoips.config.yaml_loader import load_project_config

LOG = logging.getLogger(__name__)


def _cast_env_value(value: str, target_field: str) -> Any:
    """Cast a string environment variable to the appropriate Python type.

    Handles the same casting rules as the original ``cast_string_to_bool_or_none``:
    - ``"true"`` / ``"false"`` (case-insensitive) → ``True`` / ``False``
    - ``"none"`` / ``"null"`` (case-insensitive) → ``None``
    - ``GEOIPS_REPLACE_OUTPUT_PATHS`` → ``list[str]`` (space-split)
    - ``GEOIPS_TEST_OUTPUT_CHECKER_THRESHOLD_IMAGE`` → ``float``
    - All other values → ``str``

    Parameters
    ----------
    value : str
        The raw string value from the environment variable.
    target_field : str
        The dotted path to the target field (for special-case handling).

    Returns
    -------
    Any
        The cast Python value.
    """
    if not isinstance(value, str):
        return value

    lower = value.lower()
    if lower == "true":
        return True
    if lower == "false":
        return False
    if lower in ("none", "null"):
        return None

    if target_field == "replace_output_paths":
        return value.split()

    if target_field == "test.output_checker_threshold_image":
        try:
            return float(value)
        except (ValueError, TypeError):
            return value

    return value


def _get_env_overrides() -> dict[str, Any]:
    """Read environment variables and build a nested override dictionary.

    Iterates over ``geoips.config.schema.GEOIPS_ENV_MAP``, checks each
    environment variable with ``os.getenv``, and if set, casts the
    value using ``_cast_env_value`` and inserts it at the correct
    nested path.

    Returns
    -------
    dict[str, Any]
        A (possibly nested) dictionary of overrides to apply on top of
        the default settings model.
    """
    overrides: dict[str, Any] = {}

    for env_var, field_path in GEOIPS_ENV_MAP.items():
        raw = os.getenv(env_var)
        if raw is None:
            continue

        cast = _cast_env_value(raw, field_path)
        parts = field_path.split(".")
        node = overrides
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = cast

    return overrides


def _deep_update(base: dict, override: dict) -> None:
    """Recursively update *base* dictionary with values from *override*.

    Nested dictionaries are merged rather than replaced.

    Parameters
    ----------
    base : dict
        The dictionary to update in-place.
    override : dict
        The dictionary containing override values.
    """
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_update(base[key], value)
        else:
            base[key] = value


def _compute_auto_settings(base_settings: GeoSettings) -> dict[str, Any]:
    """Compute auto-derived settings from the base model and environment.

    Resolves all paths and values that are derived at runtime:
    - ``base_path``, ``packages_dir``, ``basedir`` from source tree
    - ``outdirs`` fallback
    - ``home``, ``boxname``
    - ``testdata_dir``, ``dependencies_dir``
    - Cache directories (``cache_dir``, ``data_cache_dir``, ``satpy_data_cache_dir``)
    - Output paths resolved as absolute against ``outdirs``
    - Cache sub-paths resolved as absolute
    - Pregenerated geolocation paths resolved
    - ``replace_output_paths`` default list
    - WWW URL defaults

    Parameters
    ----------
    base_settings : GeoSettings
        The settings model with field defaults.

    Returns
    -------
    dict[str, Any]
        A (possibly nested) dictionary of auto-resolved values.
    """
    updates: dict[str, Any] = {}

    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    updates["base_path"] = base_path

    packages_dir = base_settings.packages_dir
    if not packages_dir:
        packages_dir = os.path.abspath(os.path.join(base_path, os.pardir, os.pardir))
        updates["packages_dir"] = packages_dir

    basedir = base_settings.basedir
    if not basedir:
        basedir = os.path.abspath(os.path.join(packages_dir, os.pardir))
        updates["basedir"] = basedir

    outdirs = base_settings.outdirs
    if not outdirs:
        outdirs = os.getenv("GEOIPS_OUTDIRS", "").rstrip("/")
    if not outdirs:
        LOG.warning(
            "GEOIPS_OUTDIRS is not set in your environment. "
            "Defaulting to $HOME/geoips_outdirs as output dir. "
            "Please set GEOIPS_OUTDIRS if you want to write to a "
            "different directory by default."
        )
        try:
            home_dir = os.environ.get("HOME") or os.environ.get(
                "HOMEDRIVE", ""
            ) + os.environ.get("HOMEPATH", "")
        except Exception:
            LOG.error(
                "Could not resolve environment variable $HOME, using '/' as default"
            )
            home_dir = "/"
        outdirs = os.path.join(home_dir, "geoips_outdirs")
        updates["outdirs"] = outdirs

    if not base_settings.boxname:
        updates["boxname"] = socket.gethostname()

    if not base_settings.home:
        if not os.getenv("HOME"):
            updates["home"] = os.getenv("HOMEDRIVE", "") + os.getenv("HOMEPATH", "")
        else:
            updates["home"] = os.getenv("HOME", "").rstrip("/")

    if not base_settings.testdata_dir:
        updates["testdata_dir"] = os.path.join(basedir, "test_data")
    if not base_settings.dependencies_dir:
        updates["dependencies_dir"] = os.path.join(basedir, "geoips_dependencies")

    cache_updates: dict[str, Any] = {}
    if base_settings.cache.cache_dir is None:
        cache_updates["cache_dir"] = platformdirs.user_cache_dir("geoips")
    if base_settings.cache.data_cache_dir is None:
        cache_updates["data_cache_dir"] = os.path.join(outdirs, "cache", "geoips")
    if base_settings.cache.satpy_data_cache_dir is None:
        cache_updates["satpy_data_cache_dir"] = os.path.join(outdirs, "cache", "satpy")

    dc = cache_updates.get("data_cache_dir", base_settings.cache.data_cache_dir)
    sc = cache_updates.get(
        "satpy_data_cache_dir", base_settings.cache.satpy_data_cache_dir
    )

    def _resolve(root, field):
        val = str(getattr(base_settings.cache, field))
        if not os.path.isabs(val):
            return os.path.join(root, val)
        return val

    cache_updates["data_cache_shortterm_geolocation_dynamic"] = _resolve(
        dc, "data_cache_shortterm_geolocation_dynamic"
    )
    cache_updates["data_cache_shortterm_geolocation_solar_angles"] = _resolve(
        dc, "data_cache_shortterm_geolocation_solar_angles"
    )
    cache_updates["data_cache_shortterm_calibrated_data"] = _resolve(
        dc, "data_cache_shortterm_calibrated_data"
    )
    cache_updates["data_cache_longterm_geolocation_static"] = _resolve(
        dc, "data_cache_longterm_geolocation_static"
    )
    cache_updates["satpy_cache_shortterm_calibrated_data"] = _resolve(
        sc, "satpy_cache_shortterm_calibrated_data"
    )
    cache_updates["satpy_cache_shortterm_geolocation_solar_angles"] = _resolve(
        sc, "satpy_cache_shortterm_geolocation_solar_angles"
    )

    if cache_updates:
        updates["cache"] = {
            **base_settings.cache.model_dump(),
            **cache_updates,
        }

    output_updates: dict[str, Any] = {}

    def _resolve_output(field):
        val = str(getattr(base_settings.output_paths, field))
        if not os.path.isabs(val):
            return os.path.join(outdirs, val)
        return val

    # These are the legacy output-path variables that historically did NOT use a
    # ``GEOIPS_`` prefix (e.g. ``PRESECTORED_DATA_PATH``, ``SCRATCH``, ``LOGDIR``).
    # The list mirrors every field on ``OutputPathsSettings`` and is kept in sync
    # with the schema, ``GEOIPS_ENV_MAP``, and legacy ``base_paths.py`` by
    # ``tests/unit_tests/config/test_env_map_sync.py``.
    for field_name in (
        "presectored_data",
        "preread_data",
        "preregistered_data",
        "precalculated_data",
        "clean_imagery",
        "annotated_imagery",
        "geotiff_imagery",
        "final_data",
        "pregenerated_geolocation",
        "scratch",
        "localscratch",
        "sharedscratch",
        "logdir",
        "geoipsdata",
        "ancildat_autogen",
        "ancildat",
        "tcwww",
        "tcprivatewww",
        "publicwww",
        "privatewww",
        "tc_decks_db",
        "tc_decks_dir",
    ):
        resolved = _resolve_output(field_name)
        if resolved != str(getattr(base_settings.output_paths, field_name)):
            output_updates[field_name] = resolved

    if output_updates:
        updates["output_paths"] = {
            **base_settings.output_paths.model_dump(),
            **output_updates,
        }

    for field_name, default_base in (
        ("pregenerated_static_geolocation", outdirs),
        ("pregenerated_dynamic_geolocation", outdirs),
        ("tc_template", base_path),
    ):
        val = str(getattr(base_settings, field_name))
        if not os.path.isabs(val) and field_name not in updates:
            updates[field_name] = os.path.join(default_base, val)

    www_updates: dict[str, Any] = {}
    for www_key, path_field in (
        ("tcwww_url", "tcwww"),
        ("tcprivatewww_url", "tcprivatewww"),
        ("publicwww_url", "publicwww"),
        ("privatewww_url", "privatewww"),
    ):
        if getattr(base_settings, www_key) is None:
            op = updates.get("output_paths", {}).get(
                path_field,
                getattr(base_settings.output_paths, path_field),
            )
            www_updates[www_key] = op
    if www_updates:
        updates.update(www_updates)

    if not base_settings.replace_output_paths:
        raw = os.getenv("GEOIPS_REPLACE_OUTPUT_PATHS", "")
        if raw:
            updates["replace_output_paths"] = raw.split()
        else:
            updates["replace_output_paths"] = (
                "TCWWW TCPRIVATEWWW PRIVATEWWW PUBLICWWW "
                "GEOTIFF_IMAGERY_PATH ANNOTATED_IMAGERY_PATH "
                "CLEAN_IMAGERY_PATH"
            ).split()

    return updates


class GeoIPSConfig:
    """Immutable, layered GeoIPS configuration container.

    Configuration is loaded once at construction time with this priority
    (highest wins):

    1. Environment variables (``GEOIPS_*`` and unprefixed aliases)
    2. Project-level ``.geoips.yaml`` file
    3. Pydantic model :class:`Field` defaults (lowest)

    The resulting configuration is frozen — all mutations must be done
    via ``model_copy(update=...)``, which returns a new instance.

    Parameters
    ----------
    project_config_path : str or None, optional
        Override the project config search path. If ``None``, the
        standard search locations are used.
    """

    def __init__(self, project_config_path: str | None = None) -> None:
        settings = GeoSettings(outdirs=os.getenv("GEOIPS_OUTDIRS", ""))

        auto = _compute_auto_settings(settings)
        settings_dict = settings.model_dump()
        _deep_update(settings_dict, auto)
        settings = GeoSettings.model_validate(settings_dict)

        plugin_yaml: dict[str, Any] = {}
        project_data = load_project_config()
        if project_data is not None and isinstance(project_data, dict):
            geoips_data = project_data.get("geoips")
            if isinstance(geoips_data, dict):
                raw_plugins = geoips_data.get("plugins")
                if isinstance(raw_plugins, dict):
                    plugin_yaml = raw_plugins
                settings_dict = settings.model_dump()
                _deep_update(settings_dict, geoips_data)
                settings = GeoSettings.model_validate(settings_dict)

        env_overrides = _get_env_overrides()
        if env_overrides:
            settings_dict = settings.model_dump()
            _deep_update(settings_dict, env_overrides)
            settings = GeoSettings.model_validate(settings_dict)

        self._settings = settings
        self._legacy_dict = self._build_legacy_dict()
        self._plugin_yaml = plugin_yaml
        self._plugin_cache: dict[str, Any] = {}
        self._plugins_ns: Any = None

    def _resolve_plugin(self, name: str) -> Any:
        """Resolve, validate, and cache a single plugin's settings.

        Parameters
        ----------
        name : str
            The registered plugin name.

        Returns
        -------
        pydantic.BaseModel
            The validated settings model instance for the plugin.

        Raises
        ------
        KeyError
            If no plugin with *name* is registered.
        """
        from geoips.config.plugins import (
            discover_config_plugins,
            resolve_plugin_settings,
        )

        if name in self._plugin_cache:
            return self._plugin_cache[name]
        plugins = discover_config_plugins()
        if name not in plugins:
            raise KeyError(name)
        settings = resolve_plugin_settings(plugins[name], self._plugin_yaml.get(name))
        self._plugin_cache[name] = settings
        return settings

    @property
    def plugins(self) -> Any:
        """Accessor for configuration contributed by external plugin packages.

        Returns a namespace supporting attribute access
        (``config.plugins.my_pkg``), item access (``config.plugins["my_pkg"]``),
        ``.get()``, and iteration over registered plugin names. Plugin modules
        are imported lazily on first access.
        """
        from geoips.config.plugins import (
            discover_config_plugins,
            PluginSettingsNamespace,
        )

        if self._plugins_ns is None:
            self._plugins_ns = PluginSettingsNamespace(
                self._resolve_plugin, discover_config_plugins().keys()
            )
        return self._plugins_ns

    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the inner settings model.

        Parameters
        ----------
        name : str
            Attribute name.

        Returns
        -------
        Any
            The corresponding configuration value.

        Raises
        ------
        AttributeError
            If the attribute does not exist on the settings model.
        """
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return getattr(self._settings, name)
        except AttributeError:
            raise AttributeError(f"GeoIPSConfig has no attribute {name!r}") from None

    def __getitem__(self, key: str) -> Any:
        """Dict-style access for backward compatibility.

        Parameters
        ----------
        key : str
            Legacy uppercase key (e.g. ``GEOIPS_OUTDIRS``).

        Returns
        -------
        Any
            The configuration value from the legacy dictionary.

        Raises
        ------
        KeyError
            If *key* is not a recognized legacy config key.
        """
        return self._legacy_dict[key]

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by legacy uppercase key.

        Parameters
        ----------
        key : str
            The uppercase legacy key (e.g. ``GEOIPS_OUTDIRS``).
        default : Any, optional
            Value to return if the key is not found.

        Returns
        -------
        Any
            The configuration value, or *default*.
        """
        return self._legacy_dict.get(key, default)

    def to_legacy_dict(self) -> dict[str, Any]:
        """Return the full configuration as a flat uppercase dictionary.

        This mirrors the shape of the old ``PATHS`` dict from
        ``geoips.filenames.base_paths`` for backward compatibility.

        Deprecated: The flat uppercase dictionary is a backwards-compatibility
        layer and is slated for removal in a future release. New code should
        access settings via the structured ``GeoIPSConfig`` / ``GeoSettings``
        attributes instead. ``geoips.config.schema.GEOIPS_ENV_MAP`` is the
        authoritative list of supported environment variables and settings.

        Returns
        -------
        dict[str, Any]
            Flat uppercase-keyed configuration dictionary.
        """
        warnings.warn(
            "GeoIPSConfig.to_legacy_dict() and the flat uppercase config keys "
            "are deprecated and will be removed in a future release. Access "
            "settings via the structured GeoIPSConfig attributes instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return dict(self._legacy_dict)

    def _build_legacy_dict(self) -> dict[str, Any]:
        s = self._settings
        op = s.output_paths
        ca = s.cache
        fe = s.features
        lo = s.logging
        te = s.test

        return {
            "BASE_PATH": s.base_path,
            "GEOIPS_OUTDIRS": s.outdirs,
            "GEOIPS_PACKAGES_DIR": s.packages_dir,
            "GEOIPS_REPLACE_OUTPUT_PATHS": s.replace_output_paths,
            "GEOIPS_USE_PYDANTIC": fe.use_pydantic,
            "GEOIPS_BASEDIR": s.basedir,
            "GEOIPS_DATA_CACHE_DIR": ca.data_cache_dir,
            "SATPY_DATA_CACHE_DIR": ca.satpy_data_cache_dir,
            "GEOIPS_GEOLOCATION_CACHE_BACKEND": ca.geolocation_cache_backend,
            "GEOIPS_REBUILD_REGISTRIES": fe.rebuild_registries,
            "NO_COLOR": fe.no_color,
            "GEOIPS_DOCS_URL": s.docs_url,
            "GEOIPS_VERSION": s.version,
            "GEOIPS_OPERATIONAL_USER": fe.operational_user,
            "GEOIPS_COPYRIGHT": s.copyright,
            "GEOIPS_COPYRIGHT_ABBREVIATED": s.copyright_abbreviated,
            "GEOIPS_CACHE_DIR": ca.cache_dir,
            "GEOIPS_RCFILE": s.rcfile,
            "DEFAULT_QUEUE": s.default_queue,
            "BOXNAME": s.boxname,
            "GEOIPS_LOGGING_FMT_STRING": lo.fmt_string,
            "GEOIPS_LOGGING_DATEFMT_STRING": lo.datefmt_string,
            "GEOIPS_LOGGING_LEVEL": lo.level,
            "GEOIPS_WARNING_LEVEL": s.warning_level,
            "GEOIPS_RICH_CONSOLE_OUTPUT": fe.rich_console_output,
            "GEOIPS_TEST_OUTPUT_CHECKER_THRESHOLD_IMAGE": float(
                te.output_checker_threshold_image
            ),
            "GEOIPS_TEST_PRINT_TEXT_OUTPUT_CHECKER_TO_CONSOLE": (
                te.print_text_output_checker_to_console
            ),
            "GEOIPS_TEST_PROMPT_TO_OVERWRITE_COMPARISON_FILE_IF_MISMATCH": (
                te.prompt_to_overwrite_comparison_file_if_mismatch
            ),
            "GEOIPS_TEST_SUPPRESS_PYTEST_FAILED_LOG_CONTENTS": (
                te.suppress_pytest_failed_log_contents
            ),
            "GEOIPS_TEST_SECTOR_CREATE_ANNOTATED_OUTPUTS": (
                te.sector_create_annotated_outputs
            ),
            "GEOIPS_TEST_SECTOR_CREATE_GEOTIFF_OUTPUTS": (
                te.sector_create_geotiff_outputs
            ),
            "GEOIPS_TESTDATA_DIR": s.testdata_dir,
            "GEOIPS_DEPENDENCIES_DIR": s.dependencies_dir,
            "PRESECTORED_DATA_PATH": op.presectored_data,
            "PREREAD_DATA_PATH": op.preread_data,
            "PREREGISTERED_DATA_PATH": op.preregistered_data,
            "PRECALCULATED_DATA_PATH": op.precalculated_data,
            "CLEAN_IMAGERY_PATH": op.clean_imagery,
            "ANNOTATED_IMAGERY_PATH": op.annotated_imagery,
            "GEOTIFF_IMAGERY_PATH": op.geotiff_imagery,
            "FINAL_DATA_PATH": op.final_data,
            "PREGENERATED_GEOLOCATION_PATH": op.pregenerated_geolocation,
            "GEOIPS_PREGENERATED_STATIC_GEOLOCATION": (
                s.pregenerated_static_geolocation
            ),
            "GEOIPS_PREGENERATED_DYNAMIC_GEOLOCATION": (
                s.pregenerated_dynamic_geolocation
            ),
            "SCRATCH": op.scratch,
            "LOCALSCRATCH": op.localscratch,
            "SHAREDSCRATCH": op.sharedscratch,
            "LOGDIR": op.logdir,
            "GEOIPSDATA": op.geoipsdata,
            "GEOIPS_ANCILDAT_AUTOGEN": op.ancildat_autogen,
            "GEOIPS_ANCILDAT": op.ancildat,
            "TCWWW": op.tcwww,
            "TCPRIVATEWWW": op.tcprivatewww,
            "PUBLICWWW": op.publicwww,
            "PRIVATEWWW": op.privatewww,
            "GEOIPS_TC_DECKS_DB": op.tc_decks_db,
            "GEOIPS_TC_DECKS_DIR": op.tc_decks_dir,
            "GEOIPS_TC_DECKS_TYPE": s.tc_decks_type,
            "GEOIPS_DATA_CACHE_DIR_SHORTTERM_GEOLOCATION_DYNAMIC": (
                ca.data_cache_shortterm_geolocation_dynamic
            ),
            "GEOIPS_DATA_CACHE_DIR_LONGTERM_GEOLOCATION_STATIC": (
                ca.data_cache_longterm_geolocation_static
            ),
            "GEOIPS_DATA_CACHE_DIR_SHORTTERM_GEOLOCATION_SOLAR_ANGLES": (
                ca.data_cache_shortterm_geolocation_solar_angles
            ),
            "GEOIPS_DATA_CACHE_DIR_SHORTTERM_CALIBRATED_DATA": (
                ca.data_cache_shortterm_calibrated_data
            ),
            "SATPY_DATA_CACHE_DIR_SHORTTERM_CALIBRATED_DATA": (
                ca.satpy_cache_shortterm_calibrated_data
            ),
            "SATPY_DATA_CACHE_DIR_SHORTTERM_GEOLOCATION_SOLAR_ANGLES": (
                ca.satpy_cache_shortterm_geolocation_solar_angles
            ),
            "TC_TEMPLATE": s.tc_template,
            "HOME": s.home
            or (
                os.getenv("HOME", "").rstrip("/")
                or os.getenv("HOMEDRIVE", "") + os.getenv("HOMEPATH", "")
            ),
            "TCWWW_URL": s.tcwww_url or op.tcwww,
            "TCPRIVATEWWW_URL": s.tcprivatewww_url or op.tcprivatewww,
            "PUBLICWWW_URL": s.publicwww_url or op.publicwww,
            "PRIVATEWWW_URL": s.privatewww_url or op.privatewww,
        }


_config: GeoIPSConfig | None = None


def get_config(project_config_path: str | None = None) -> GeoIPSConfig:
    """Return the singleton :class:`GeoIPSConfig` instance.

    Creates the configuration on first call. Subsequent calls return
    the cached instance.

    Parameters
    ----------
    project_config_path : str or None, optional
        Override the project config search path (only used on first call).

    Returns
    -------
    GeoIPSConfig
        The singleton configuration instance.
    """
    global _config
    if _config is None:
        _config = GeoIPSConfig(project_config_path=project_config_path)
    return _config


def make_dirs(path: str) -> str:
    """Create directories, catching exceptions if directory already exists.

    Parameters
    ----------
    path : str
        Path to directory to create.

    Returns
    -------
    str
        *path* if successfully created.
    """
    LOG.info("Creating directory %s if it doesn't already exist.", path)
    os.makedirs(path, mode=0o755, exist_ok=True)
    return path
