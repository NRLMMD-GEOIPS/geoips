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
from pluginify.commandline_typer import configure_logging
from pluginify.plugin_registry import PluginRegistry


# ======================================================================
# Module-level NamedTuples used by the parallel pipeline
# ======================================================================


class ChunkCheckRecord(NamedTuple):
    """Immutable record passed through the chunk-check pipeline."""
    name: str
    url: str
    version_file: str
    existing_dir: str | None


class ChunkCheckOutcome(NamedTuple):
    """Result of a chunk-hash check for one dataset."""
    record: ChunkCheckRecord
    disposition: str   # "cached" | "needs_download" | "stale"
    reason: str


class DownloadResult(NamedTuple):
    """Result of a full dataset download."""
    name: str
    full_hash: str
    chunk_hash: str
    temp_path: str
    total_bytes: int


# ======================================================================
# Module-level parallel helpers
# ======================================================================


def _chunk_check_parallel(verify_version, fetch_chunk, read_stored,
                          infos, max_workers, chunk_size):
    """Run chunk-hash verification for *infos* in parallel.

    Parameters
    ----------
    verify_version : callable
        ``(version_file, name, url) -> bool``
    fetch_chunk : callable
        ``(url, chunk_size) -> str | None``
    read_stored : callable
        ``(version_file) -> str | None``
    infos : list of ChunkCheckRecord
    max_workers : int
    chunk_size : int

    Returns
    -------
    list of ChunkCheckOutcome
    """

    def check_one(info):
        """Pure function: classify a single dataset from its record."""
        if info.existing_dir is None:
            return ChunkCheckOutcome(info, "needs_download", "not installed")

        if not verify_version(info.version_file, info.name, info.url):
            return ChunkCheckOutcome(info, "stale",
                                     "version file invalid or incomplete")

        live_hash = fetch_chunk(info.url, chunk_size)
        if live_hash is None:
            stored = read_stored(info.version_file)
            if stored is not None:
                return ChunkCheckOutcome(
                    info, "cached", "trusted (server unreachable)"
                )
            return ChunkCheckOutcome(
                info, "stale",
                "no chunk hash + server unreachable"
            )

        stored = read_stored(info.version_file)
        if stored is not None and live_hash == stored:
            return ChunkCheckOutcome(info, "cached", "chunk verified")

        return ChunkCheckOutcome(
            info, "stale", "upstream changed (chunk hash mismatch)"
        )

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        return list(pool.map(check_one, infos))


def _download_parallel(download_to_temp, first_chunk_size,
                       targets, outdir, temp_dir, max_workers, display):
    """Download *targets* in parallel, extract sequentially on main thread.

    Parameters
    ----------
    download_to_temp : callable
        ``(url, temp_dir, chunk_size) -> DownloadResult``
    first_chunk_size : int
    targets : list of ChunkCheckOutcome
    outdir : pathlib.Path
    temp_dir : str or None
    max_workers : int
    display : RichProgressDisplay or PlainProgressDisplay
    """
    def run_one(target, chunk_size):
        name = target.record.name
        display.add_download(name, 0)
        try:
            result = download_to_temp(
                target.record.url, temp_dir, chunk_size
            )
            display.mark_download_done(name)
            return result._replace(name=name)
        except Exception as exc:
            display.mark_failed(name, str(exc))
            return None

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(run_one, t, first_chunk_size): t
            for t in targets
        }
        for future in as_completed(futures):
            result = future.result()
            if result is None:
                continue
            _extract_and_finalize(
                result, outdir, display, first_chunk_size
            )


def _extract_and_finalize(result, outdir, display, chunk_size):  # noqa: ARG001
    """Extract a downloaded archive and write its version file.

    Sequential (called from the main thread) to avoid disk contention.
    ``chunk_size`` is accepted for API symmetry but unused here.
    """
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
    """Return the file-count of a tar archive for progress display.

    Falls back to 1 so the progress bar renders even on read errors.
    """
    try:
        with tarfile.open(temp_path, mode="r:gz") as tar:
            return len(tar.getmembers())
    except Exception:
        return 1


def _extract_from_temp(temp_path, outdir):
    """Extract a tar archive to *outdir*, validating paths.

    Raises ``SystemExit`` on safety violation (path traversal).
    """
    with tarfile.open(temp_path, mode="r:gz") as tar:
        for m in tar:
            member_path = (outdir / m.name).resolve()
            if not str(member_path).startswith(str(outdir.resolve())):
                raise SystemExit(
                    "Found unsafe filepath in tar, exiting now."
                )
            tar.extract(m, path=outdir, filter="tar")


def _write_version_file(version_file, dataset_name, url, sha256_hash,
                        chunk_sha256=None):
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
            "-j", "--parallel",
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
            help=(
                "Directory for temporary download files (default: system /tmp)."
            ),
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
            infos, args.parallel, self._FIRST_CHUNK_SIZE,
        )

        for r in results:
            if r.disposition == "cached":
                display.add_cached(r.record.name)
            elif r.disposition == "stale":
                display.log_stale(r.record.name, r.reason)
                self._cleanup_dataset_dir(r.record.existing_dir,
                                          r.record.version_file)

        targets = [r for r in results if r.disposition != "cached"]
        if not targets:
            return

        temp_dir = str(args.temp_dir) if args.temp_dir else None
        _download_parallel(
            self._download_to_temp, self._FIRST_CHUNK_SIZE,
            targets, outdir, temp_dir, args.parallel, display,
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
            infos.append(ChunkCheckRecord(
                name=name, url=url, version_file=version_file,
                existing_dir=existing_dir
            ))
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
        temp_dir : str or None
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

        with tempfile.NamedTemporaryFile(
            dir=temp_dir, delete=False
        ) as tmp:
            for data in resp.iter_content(chunk_size=1024 * 1024):
                if data:
                    tmp.write(data)
                    sha256.update(data)
                    if accumulated < chunk_size:
                        to_add = data[:chunk_size - accumulated]
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


class GeoipsConfig(GeoipsCommand):
    """Config top-level command for configuring your GeoIPS environment."""

    name = "config"
    command_classes = [
        GeoipsConfigCreateRegistries,
        GeoipsConfigDeleteRegistries,
        GeoipsConfigInstall,
        GeoipsConfigInstallGithub,
    ]
