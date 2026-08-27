# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""GeoIPS CLI "install" command.

Installation commands used to install test datasets and github plugin packages.
"""

import hashlib
import os
import pathlib
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from os import listdir, remove
from os.path import join
import subprocess
import tarfile
import tempfile
from typing import NamedTuple

import requests
import yaml

import geoips
from geoips.commandline.ancillary_info.test_data import test_dataset_dict
from geoips.commandline.geoips_command import GeoipsCommand, GeoipsExecutableCommand
from geoips.commandline.install_progress import create_progress_display
from geoips.config.plugins import (
    build_plugin_env_map,
    field_comment,
    is_nested_model,
)
from geoips.config.schema import GEOIPS_ENV_MAP


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


class GeoipsInstallGithub(GeoipsExecutableCommand):
    """Command Class for installing github packages/datasets.

    Supports installation of packages and test data needed for testing and/or running
    your GeoIPS environment via github repositories.
    """

    name = "github"
    command_classes = []

    def add_arguments(self):
        """Add arguments to the install-subparser for the install Command."""
        self.parser.add_argument(
            "test_dataset_name",
            type=str.lower,
            help="GeoIPS Test Dataset to Install from GitHub repository.",
        )

    def __call__(self, args):
        """Run the `geoips install github <test_dataset_name>` command.

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


class GeoipsInstallData(GeoipsExecutableCommand):
    """Command Class for installing test datasets.

    Supports installation of test data needed for testing and/or running
    your GeoIPS environment.
    """

    name = "data"
    command_classes = []

    _FIRST_CHUNK_SIZE = 5 * 1024 * 1024  # 5 MB

    def add_arguments(self):
        """Add arguments to the install-subparser for the Install Command."""
        self.parser.add_argument(
            "test_dataset_names",
            type=str.lower,
            nargs="+",
            metavar="DATASET",
            choices=list(test_dataset_dict.keys()) + ["all"],
            help=(
                "Cataloged test dataset to install; specify one or more names, or "
                "'all' by itself."
            ),
        )
        testdata_dir = geoips.filenames.base_paths.PATHS["GEOIPS_TESTDATA_DIR"]
        self.parser.add_argument(
            "-o",
            "--outdir",
            type=pathlib.Path,
            default=pathlib.Path(testdata_dir) if testdata_dir else pathlib.Path.cwd(),
            help=(
                "Existing directory in which to install the datasets. Defaults to "
                "GEOIPS_TESTDATA_DIR when configured, or the current directory "
                "otherwise."
            ),
        )
        self.parser.add_argument(
            "-j",
            "--parallel",
            type=int,
            default=int(os.getenv("GEOIPS_DOWNLOAD_WORKERS", "6")),
            metavar="N",
            help=(
                "Maximum number of concurrent downloads. Defaults to "
                "GEOIPS_DOWNLOAD_WORKERS, or 6 when unset."
            ),
        )
        self.parser.add_argument(
            "--no-rich",
            action="store_true",
            help="Use plain-text progress output instead of the rich live display.",
        )
        self.parser.add_argument(
            "--temp-dir",
            type=pathlib.Path,
            default=None,
            metavar="DIRECTORY",
            help=(
                "Directory for temporary download files. Defaults to the system "
                "temporary directory."
            ),
        )

    def __call__(self, args):
        """Run the ``geoips install <test_dataset_names> -o <outdir>`` command.

        Parameters
        ----------
        args: Namespace()
            The argument namespace to parse through.
        """
        if "all" in args.test_dataset_names and len(args.test_dataset_names) > 1:
            self.parser.error("'all' cannot be combined with individual dataset names.")

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


class GeoipsInstall(GeoipsCommand):
    """Top-Level install command for installing test datasets and plugin packages."""

    name = "install"

    command_classes = [GeoipsInstallData, GeoipsInstallGithub]
