# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""GeoIPS CLI "config" command.

Various configuration-based commands for setting up your geoips environment.
"""

import hashlib
import os
import pathlib
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from importlib import metadata
from os import listdir, remove
from os.path import join
import subprocess
import tarfile
import tempfile
from typing import NamedTuple

import requests
import yaml
from pydantic import ValidationError

import geoips
from geoips.commandline.ancillary_info.test_data import test_dataset_dict
from geoips.commandline.geoips_command import GeoipsCommand, GeoipsExecutableCommand
from geoips.commandline.install_progress import create_progress_display
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
from pluginify.commandline_typer import configure_logging
from pluginify.plugin_registry import PluginRegistry


class ChunkCheckRecord(NamedTuple):
    """Immutable record passed through the chunk-check pipeline."""

    name: str
    url: str
    version_file: str
    existing_dir: str | None


class ChunkCheckOutcome(NamedTuple):
    """Result of a chunk-hash check for one dataset."""

    record: ChunkCheckRecord
    disposition: str  # "cached" | "needs_download" | "stale"
    reason: str


class DownloadResult(NamedTuple):
    """Result of a full dataset download."""

    name: str
    full_hash: str
    chunk_hash: str
    temp_path: str
    total_bytes: int


def _chunk_check_parallel(
    verify_version, fetch_chunk, read_stored, infos, max_workers, chunk_size
):
    """Run chunk-hash verification for *infos* in parallel."""

    def check_one(info):
        """Pure function: classify a single dataset from its record."""
        if info.existing_dir is None:
            return ChunkCheckOutcome(info, "needs_download", "not installed")

        if not verify_version(info.version_file, info.name, info.url):
            return ChunkCheckOutcome(
                info, "stale", "version file invalid or incomplete"
            )

        live_hash = fetch_chunk(info.url, chunk_size)
        if live_hash is None:
            stored = read_stored(info.version_file)
            if stored is not None:
                return ChunkCheckOutcome(info, "cached", "trusted (server unreachable)")
            return ChunkCheckOutcome(
                info, "stale", "no chunk hash + server unreachable"
            )

        stored = read_stored(info.version_file)
        if stored is not None and live_hash == stored:
            return ChunkCheckOutcome(info, "cached", "chunk verified")

        return ChunkCheckOutcome(
            info, "stale", "upstream changed (chunk hash mismatch)"
        )

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        return list(pool.map(check_one, infos))


def _download_parallel(
    download_to_temp, first_chunk_size, targets, outdir, temp_dir, max_workers, display
):
    """Download *targets* in parallel, extract sequentially on main thread."""

    def run_one(target, chunk_size):
        name = target.record.name
        display.add_download(name, 0)
        try:
            result = download_to_temp(target.record.url, temp_dir, chunk_size)
            display.mark_download_done(name)
            return result._replace(name=name)
        except Exception as exc:
            display.mark_failed(name, str(exc))
            return None

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(run_one, t, first_chunk_size): t for t in targets}
        for future in as_completed(futures):
            result = future.result()
            if result is None:
                continue
            _extract_and_finalize(result, outdir, display, first_chunk_size)


def _extract_and_finalize(result, outdir, display, chunk_size):  # noqa: ARG001
    """Extract a downloaded archive and write its version file."""
    name = result.name
    total = _count_tar_members(result.temp_path)
    display.add_extract(name, total)

    try:
        _extract_from_temp(result.temp_path, outdir)
        display.update_extract(name, total, total)
        _write_version_file(
            join(outdir, f".{name}_version"),
            name,
            test_dataset_dict[name],
            result.full_hash,
            result.chunk_hash,
        )
        display.mark_complete(name)
    except Exception as exc:
        display.mark_failed(name, str(exc))
    finally:
        try:
            remove(result.temp_path)
        except OSError:
            pass


def _count_tar_members(temp_path):
    """Return the file-count of a tar archive for progress display."""
    try:
        with tarfile.open(temp_path, mode="r:gz") as tar:
            return len(tar.getmembers())
    except Exception:
        return 1


def _extract_from_temp(temp_path, outdir):
    """Extract a tar archive to *outdir*, validating paths."""
    with tarfile.open(temp_path, mode="r:gz") as tar:
        for m in tar:
            member_path = (outdir / m.name).resolve()
            if not str(member_path).startswith(str(outdir.resolve())):
                raise SystemExit("Found unsafe filepath in tar, exiting now.")
            tar.extract(m, path=outdir, filter="tar")


def _write_version_file(
    version_file, dataset_name, url, sha256_hash, chunk_sha256=None
):
    """Write a ``.geoips_testdata_version`` file recording the download."""
    data = {
        "dataset": dataset_name,
        "url": url,
        "sha256": sha256_hash,
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
    }
    if chunk_sha256:
        data["chunk_sha256"] = chunk_sha256
    with open(version_file, "w") as fh:
        yaml.safe_dump(data, fh, default_flow_style=False)


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
    overrides: dict[str, str], keys_to_prompt: list[str]
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


class GeoipsConfigCreateRegistries(GeoipsExecutableCommand):
    """Config Command Class for creating plugin registries for plugin packages."""

    name = "create-registries"
    command_classes = []

    def add_arguments(self):
        """Add arguments to the config-subparser for the Config Command."""
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
        """Run the `geoips config create-registries -n <namespace> -s <save_type> -p <packages>` command.  # NOQA

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


class GeoipsConfigDeleteRegistries(GeoipsExecutableCommand):
    """Config Command Class for deleting plugin registries for plugin packages."""

    name = "delete-registries"
    command_classes = []

    def add_arguments(self):
        """Add arguments to the config-subparser for the Config Command."""
        pass

    def __call__(self, args):
        """Run the `geoips config delete-registries -n <namespace> -p <packages>` command.  # NOQA

        Parameters
        ----------
        args: Namespace()
            - The argument namespace to parse through
        """
        packages = args.packages
        namespace = args.namespace
        # This is needed to ensure that we capture the logs from pluginify
        configure_logging()
        plugin_registry = PluginRegistry(namespace)
        plugin_registry.delete_registries(packages)


class GeoipsConfigInstall(GeoipsExecutableCommand):
    """Config Command Class for installing packages/data.

    Supports installation of packages and test data needed for testing and/or running
    your GeoIPS environment.
    """

    name = "install"
    command_classes = []

    _FIRST_CHUNK_SIZE = 5 * 1024 * 1024  # 5 MB

    def add_arguments(self):
        """Add arguments to the config-subparser for the Config Command."""
        self.parser.add_argument(
            "test_dataset_names",
            type=str.lower,
            nargs="+",
            choices=list(test_dataset_dict.keys()) + ["all"],
            help=(
                "Names of the GeoIPS test datasets to install. If 'all' is specified, "
                "GeoIPS will install all test datasets hosted on NextCloud. 'all' "
                "cannot be specified alongside other test dataset names."
            ),
        )
        testdata_dir = geoips.filenames.base_paths.PATHS["GEOIPS_TESTDATA_DIR"]
        self.parser.add_argument(
            "-o",
            "--outdir",
            type=pathlib.Path,
            default=pathlib.Path(testdata_dir) if testdata_dir else pathlib.Path.cwd(),
            help=(
                "The full path to the directory you want to install this data to."
                "If not provided, this command will default to $GEOIPS_TESTDATA_DIR"
                "if set else will default to the current working directory."
            ),
        )
        self.parser.add_argument(
            "-j",
            "--parallel",
            type=int,
            default=int(os.getenv("GEOIPS_DOWNLOAD_WORKERS", "6")),
            metavar="N",
            help=(
                "Number of concurrent downloads (env: GEOIPS_DOWNLOAD_WORKERS, "
                "default: 6)."
            ),
        )
        self.parser.add_argument(
            "--no-rich",
            action="store_true",
            help=(
                "Disable rich live progress display.  Plain text output "
                "suitable for CI logs or redirected stdout."
            ),
        )
        self.parser.add_argument(
            "--temp-dir",
            type=pathlib.Path,
            default=None,
            help=("Directory for temporary download files (default: system /tmp)."),
        )

    def __call__(self, args):
        """Run the ``geoips config install <test_dataset_names> -o <outdir>`` command.

        Parameters
        ----------
        args: Namespace()
            The argument namespace to parse through.
        """
        outdir = args.outdir
        if not outdir.is_dir():
            self.parser.error(f"Specified output directory {outdir} doesn't exist.")
            raise FileNotFoundError(outdir)

        names = self._resolve_dataset_names(args.test_dataset_names)
        display = create_progress_display(
            total=len(names),
            use_rich=not args.no_rich,
            is_tty=sys.stdout.isatty(),
        )
        display.start()
        try:
            self._install_pipeline(names, outdir, args, display)
        finally:
            display.stop()

    # ------------------------------------------------------------------
    # Pipeline orchestration
    # ------------------------------------------------------------------

    def _install_pipeline(self, names, outdir, args, display):
        """Orchestrate the full install pipeline."""
        infos = self._build_dataset_infos(names, outdir)

        results = _chunk_check_parallel(
            self._verify_version_file,
            self._fetch_first_chunk_hash,
            self._read_stored_chunk_hash,
            infos,
            args.parallel,
            self._FIRST_CHUNK_SIZE,
        )

        for r in results:
            if r.disposition == "cached":
                display.add_cached(r.record.name)
            elif r.disposition == "stale":
                display.log_stale(r.record.name, r.reason)
                self._cleanup_dataset_dir(r.record.existing_dir, r.record.version_file)

        targets = [r for r in results if r.disposition != "cached"]
        if not targets:
            return

        temp_dir = str(args.temp_dir) if args.temp_dir else None
        _download_parallel(
            self._download_to_temp,
            self._FIRST_CHUNK_SIZE,
            targets,
            outdir,
            temp_dir,
            args.parallel,
            display,
        )

    @staticmethod
    def _resolve_dataset_names(test_dataset_names):
        """Resolve ``all`` into the full list of known dataset names."""
        if "all" in test_dataset_names:
            return list(test_dataset_dict.keys())
        return test_dataset_names

    def _build_dataset_infos(self, names, outdir):
        """Create internal :class:`ChunkCheckRecord` entries for each dataset."""
        infos = []
        for name in names:
            url = test_dataset_dict[name]
            version_file = join(outdir, f".{name}_version")
            existing_dir = self._find_existing_dataset_dir(outdir, name)
            infos.append(
                ChunkCheckRecord(
                    name=name,
                    url=url,
                    version_file=version_file,
                    existing_dir=existing_dir,
                )
            )
        return infos

    @staticmethod
    def _read_stored_chunk_hash(version_file):
        """Read the stored *chunk_sha256* from a version file.

        Returns the hex string or None if the field is missing or unreadable.
        """
        try:
            with open(version_file, "r") as fh:
                data = yaml.safe_load(fh)
            return data.get("chunk_sha256") if isinstance(data, dict) else None
        except Exception:
            return None

    @staticmethod
    def _fetch_first_chunk_hash(url, chunk_size):
        """Download the first *chunk_size* bytes of *url* and return its SHA256.

        Uses an HTTP Range request (``bytes=0-{chunk_size-1}``).  If the server
        does not support ranges this method still works — the response body is
        just truncated in the hash loop.

        Parameters
        ----------
        url : str
            The test dataset URL.
        chunk_size : int
            Number of bytes to download.

        Returns
        -------
        str or None
            Hex digest of the first *chunk_size* bytes, or None on any failure
            (network error, non-2xx status, timeout, etc.).
        """
        try:
            headers = {"Range": f"bytes=0-{chunk_size - 1}"}
            resp = requests.get(url, headers=headers, stream=True, timeout=30)
            if resp.status_code not in (200, 206):
                return None

            hasher = hashlib.sha256()
            received = 0
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    remaining = chunk_size - received
                    if remaining <= 0:
                        break
                    to_hash = chunk[:remaining]
                    hasher.update(to_hash)
                    received += len(to_hash)
            return hasher.hexdigest()
        except Exception:
            return None

    @staticmethod
    def _find_existing_dataset_dir(outdir, dataset_name):
        """Find an existing dataset directory matching *dataset_name* under *outdir*.

        Returns the path to the dataset directory if found, else None.
        """
        try:
            for entry in listdir(outdir):
                if dataset_name in entry:
                    full_path = join(outdir, entry)
                    if pathlib.Path(full_path).is_dir():
                        return full_path
        except FileNotFoundError:
            pass
        return None

    @staticmethod
    def _verify_version_file(version_file, dataset_name, expected_url):
        """Verify that *version_file* exists, is valid, and matches *expected_url*.

        Also checks that the dataset directory is non-empty to guard against
        partially extracted archives.

        Returns True if the cached dataset appears valid, False otherwise.
        """
        if not pathlib.Path(version_file).is_file():
            return False
        try:
            with open(version_file, "r") as fh:
                data = yaml.safe_load(fh)
            if not isinstance(data, dict):
                return False
            if data.get("dataset") != dataset_name:
                return False
            if data.get("url") != expected_url:
                return False
            if "chunk_sha256" not in data:
                return False
            if "sha256" not in data:
                return False
            return True
        except Exception:
            return False

    @staticmethod
    def _cleanup_dataset_dir(dataset_dir, version_file):
        """Remove the dataset directory and its version file."""
        if dataset_dir and pathlib.Path(dataset_dir).is_dir():
            shutil.rmtree(dataset_dir, ignore_errors=True)
        if pathlib.Path(version_file).is_file():
            remove(version_file)

    # ------------------------------------------------------------------
    # Download to temp (functional, called from worker threads)
    # ------------------------------------------------------------------

    @staticmethod
    def _download_to_temp(url, temp_dir, chunk_size):
        """Download *url* to a temporary file and return hashes + path.

        Parameters
        ----------
        url : str
            URL of the dataset archive to download.
        temp_dir : str or None
            Directory for the temporary file (None for system default).
        chunk_size : int
            Bytes to capture for the chunk hash.

        Returns
        -------
        DownloadResult
            Populated with ``full_hash``, ``chunk_hash``, ``temp_path``.
            The ``name`` field is not set (caller fills it).

        Raises
        ------
        requests.HTTPError
            On non-2xx status.
        """
        sha256 = hashlib.sha256()
        chunk_hash = hashlib.sha256()
        accumulated = 0

        resp = requests.get(url, stream=True, timeout=(15, 300))
        resp.raise_for_status()
        total_size = int(resp.headers.get("Content-Length", 0))

        with tempfile.NamedTemporaryFile(dir=temp_dir, delete=False) as tmp:
            for data in resp.iter_content(chunk_size=1024 * 1024):
                if data:
                    tmp.write(data)
                    sha256.update(data)
                    if accumulated < chunk_size:
                        to_add = data[: chunk_size - accumulated]
                        chunk_hash.update(to_add)
                        accumulated += len(to_add)
            temp_path = tmp.name

        return DownloadResult(
            name="",
            full_hash=sha256.hexdigest(),
            chunk_hash=chunk_hash.hexdigest(),
            temp_path=temp_path,
            total_bytes=total_size,
        )


class GeoipsConfigInstallGithub(GeoipsExecutableCommand):
    """Config Command Class for installing packages/data.

    Supports installation of packages and test data needed for testing and/or running
    your GeoIPS environment via github repositories.
    """

    name = "install-github"
    command_classes = []

    def add_arguments(self):
        """Add arguments to the config-subparser for the Config Command."""
        self.parser.add_argument(
            "test_dataset_name",
            type=str.lower,
            help="GeoIPS Test Dataset to Install from GitHub repository.",
        )

    def __call__(self, args):
        """Run the `geoips config install-github <test_dataset_name>` command.

        Parameters
        ----------
        args: Namespace()
            - The argument namespace to parse through
        """
        test_dataset_name = args.test_dataset_name
        print(
            f"Running check_system_requirements.sh test_data_github {test_dataset_name}"
        )
        call_list = [
            "bash",
            join(
                geoips.filenames.base_paths.PATHS["GEOIPS_PACKAGES_DIR"],
                "geoips",
                "setup",
                "check_system_requirements.sh",
            ),
            "test_data_github",
            test_dataset_name,
        ]
        retval = subprocess.call(call_list)
        if retval != 0:
            raise IOError(f"FAILED Did not successfully install '{test_dataset_name}'")


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
        GeoipsConfigCreateRegistries,
        GeoipsConfigDeleteRegistries,
        GeoipsConfigInstall,
        GeoipsConfigInstallGithub,
        GeoipsConfigValidate,
    ]
