# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""GeoIPS CLI "config" command.

Various configuration-based commands for setting up your geoips environment.
"""

import pathlib
import subprocess
from functools import partial
from typing import Iterator, List, Tuple, BinaryIO
import io

import requests
import tarfile
from numpy import any
from tqdm import tqdm

import geoips
from geoips.commandline.ancillary_info.test_data import test_dataset_dict
from geoips.commandline.geoips_command import (
    GeoipsCommand, 
    GeoipsExecutableCommand
)
from geoips.plugin_registry import PluginRegistry


class ProgressStream:
    """Wrapper for streaming with progress tracking."""
    
    def __init__(self, response: requests.Response, chunk_size: int = 1024 * 1024):
        """Initialize progress stream.
        
        Parameters
        ----------
        response : requests.Response
            HTTP response object to stream from.
        chunk_size : int, optional
            Size of chunks to read, by default 1024*1024.
        """
        self.response = response
        self.chunk_size = chunk_size
        self.total_size = int(response.headers.get("Content-Length", 0))
        self.progress = tqdm(
            total=self.total_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            desc="Downloading & Extracting",
        )
        self._buffer = io.BytesIO()
        self._iterator = response.iter_content(chunk_size=chunk_size)
        
    def read(self, size: int = -1) -> bytes:
        """Read data from stream with progress tracking.
        
        Parameters
        ----------
        size : int, optional
            Number of bytes to read, by default -1 (all).
            
        Returns
        -------
        bytes
            Data read from stream.
        """
        if size == -1 or size is None:
            # Read all remaining data
            data = b""
            while True:
                chunk = self._read_chunk()
                if not chunk:
                    break
                data += chunk
            return data
        else:
            # Read specific amount
            return self._read_chunk(size)
    
    def _read_chunk(self, size: int = None) -> bytes:
        """Read a chunk from the iterator.
        
        Parameters
        ----------
        size : int, optional
            Size of chunk to read.
            
        Returns
        -------
        bytes
            Chunk data.
        """
        try:
            chunk = next(self._iterator)
            if chunk:
                self.progress.update(len(chunk))
                return chunk
            return b""
        except StopIteration:
            return b""
    
    def close(self):
        """Close the progress stream."""
        self.progress.close()
        self.response.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def _validate_output_directory(outdir: pathlib.Path) -> None:
    """Validate that output directory exists.
    
    Parameters
    ----------
    outdir : pathlib.Path
        The directory path to validate.
        
    Raises
    ------
    FileNotFoundError
        If the directory doesn't exist.
    """
    if not outdir.is_dir():
        raise FileNotFoundError(f"Directory {outdir} doesn't exist.")


def _validate_dataset_names(test_dataset_names: List[str]) -> None:
    """Validate test dataset name arguments.
    
    Parameters
    ----------
    test_dataset_names : List[str]
        List of dataset names to validate.
        
    Raises
    ------
    ValueError
        If 'all' is specified with other dataset names.
    """
    if len(test_dataset_names) > 1 and "all" in test_dataset_names:
        raise ValueError(
            "You cannot specify 'all' alongside other test dataset names. "
            "If 'all' is specified, that must be the only argument provided."
        )


def _get_install_dataset_names(test_dataset_names: List[str]) -> List[str]:
    """Get the list of datasets to install.
    
    Parameters
    ----------
    test_dataset_names : List[str]
        User-specified dataset names.
        
    Returns
    -------
    List[str]
        Resolved list of dataset names to install.
    """
    all_datasets = len(test_dataset_names) == 1 and test_dataset_names[0] == "all"
    return list(test_dataset_dict.keys()) if all_datasets else test_dataset_names


def _dataset_exists(dataset_name: str, outdir: pathlib.Path) -> bool:
    """Check if dataset already exists in output directory.
    
    Parameters
    ----------
    dataset_name : str
        Name of the dataset to check.
    outdir : pathlib.Path
        Output directory to check in.
        
    Returns
    -------
    bool
        True if dataset exists, False otherwise.
    """
    return any([dataset_name in fol.name for fol in outdir.iterdir() 
                if fol.is_dir()])


def _create_download_session() -> requests.Session:
    """Create a configured session for downloading.
    
    Returns
    -------
    requests.Session
        Configured session with appropriate headers.
    """
    session = requests.Session()
    session.headers.update({
        "User-Agent": "geoips-config/1.0.0",
        "Connection": "close"
    })
    return session


def _is_safe_path(filepath: str, base_dir: pathlib.Path) -> bool:
    """Check if extraction path is safe.
    
    Parameters
    ----------
    filepath : str
        File path to validate.
    base_dir : pathlib.Path
        Base directory for extraction.
        
    Returns
    -------
    bool
        True if path is safe, False otherwise.
    """
    resolved_path = (base_dir / filepath).resolve()
    return str(resolved_path).startswith(str(base_dir.resolve()))


def _iter_tar_stream(tar_stream: BinaryIO) -> Iterator[Tuple[pathlib.Path, BinaryIO]]:
    """Iterate over files in a streaming tar archive.
    
    Parameters
    ----------
    tar_stream : BinaryIO
        Stream containing tar data.
        
    Yields
    ------
    Tuple[pathlib.Path, BinaryIO]
        Path and file object for each file in archive.
    """
    with tarfile.open(fileobj=tar_stream, mode='r|*') as tfile:
        for member in tfile:
            if member.isfile():
                path = pathlib.Path(member.name)
                file_obj = tfile.extractfile(member)
                if file_obj:
                    yield path, file_obj


def _extract_tar_stream_safely(url: str, download_dir: pathlib.Path) -> None:
    """Extract tar stream safely to directory.
    
    Parameters
    ----------
    url : str
        URL to download tar from.
    download_dir : pathlib.Path
        Directory to extract to.
        
    Raises
    ------
    SystemExit
        If unsafe filepath found in tar.
    requests.RequestException
        If download fails.
    """
    session = _create_download_session()
    
    try:
        response = session.get(url, stream=True, timeout=15)
        if response.status_code != 200:
            raise requests.RequestException(
                f"Error retrieving data from {url}; "
                f"Status Code {response.status_code}."
            )
        
        with ProgressStream(response) as progress_stream:
            file_count = 0
            
            for file_path, file_obj in _iter_tar_stream(progress_stream):
                # Validate path safety
                if not _is_safe_path(str(file_path), download_dir):
                    raise SystemExit("Found unsafe filepath in tar, exiting now.")
                
                # Create output path
                output_path = download_dir / file_path
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Write file content
                with output_path.open('wb') as out_file:
                    while True:
                        chunk = file_obj.read(8192)
                        if not chunk:
                            break
                        out_file.write(chunk)
                
                file_count += 1
            
            print(f"Extracted {file_count} files")
            
    finally:
        session.close()


def _download_and_extract(url: str, download_dir: pathlib.Path) -> None:
    """Download and extract test data from URL.
    
    Parameters
    ----------
    url : str
        URL to download from.
    download_dir : pathlib.Path
        Directory to extract to.
    """
    print("Beginning streaming download and extraction...")
    _extract_tar_stream_safely(url, download_dir)


def _install_single_dataset(dataset_name: str, outdir: pathlib.Path) -> None:
    """Install a single test dataset.
    
    Parameters
    ----------
    dataset_name : str
        Name of dataset to install.
    outdir : pathlib.Path
        Output directory for installation.
    """
    if _dataset_exists(dataset_name, outdir):
        print(
            f"Test dataset '{dataset_name}' already exists under "
            f"'{outdir / dataset_name}*/'. See that "
            "location for the contents of the test dataset."
        )
        return
    
    print(
        f"Installing {dataset_name} test dataset. This may take a "
        "while..."
    )
    
    dataset_url = test_dataset_dict[dataset_name]
    _download_and_extract(dataset_url, outdir)
    
    print(
        f"Test dataset '{dataset_name}' has been installed under "
        f"{outdir}/{dataset_name}/"
    )


def _get_default_testdata_dir() -> pathlib.Path:
    """Get default test data directory.
    
    Returns
    -------
    pathlib.Path
        Default test data directory path.
    """
    testdata_dir = geoips.filenames.base_paths.PATHS["GEOIPS_TESTDATA_DIR"]
    return pathlib.Path(testdata_dir) if testdata_dir else pathlib.Path.cwd()


def _build_github_install_command(test_dataset_name: str) -> List[str]:
    """Build command list for GitHub installation.
    
    Parameters
    ----------
    test_dataset_name : str
        Name of test dataset to install.
        
    Returns
    -------
    List[str]
        Command list for subprocess.
    """
    script_path = (
        pathlib.Path(geoips.filenames.base_paths.PATHS["GEOIPS_TESTDATA_DIR"]) /
        "geoips" / "setup" / "check_system_requirements.sh"
    )
    
    return [
        "bash",
        str(script_path),
        "test_data_github",
        test_dataset_name,
    ]


class GeoipsConfigCreateRegistries(GeoipsExecutableCommand):
    """Config Command Class for creating plugin registries."""

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
                "The file format to save the registry as. Defaults to 'json', "
                "which is what's used by GeoIPS under the hood. For human "
                "readable output, you can provide the optional argument "
                "'-s yaml'."
            ),
        )

    def __call__(self, args):
        """Run create-registries command.

        Parameters
        ----------
        args : Namespace
            The argument namespace to parse through.
        """
        plugin_registry = PluginRegistry(args.namespace)
        result = plugin_registry.create_registries(args.packages, args.save_type)
        print(result)


class GeoipsConfigDeleteRegistries(GeoipsExecutableCommand):
    """Config Command Class for deleting plugin registries."""

    name = "delete-registries"
    command_classes = []

    def add_arguments(self):
        """Add arguments to the config-subparser for the Config Command."""
        pass

    def __call__(self, args):
        """Run delete-registries command.

        Parameters
        ----------
        args : Namespace
            The argument namespace to parse through.
        """
        plugin_registry = PluginRegistry(args.namespace)
        result = plugin_registry.delete_registries(args.packages)
        print(result)


class GeoipsConfigInstall(GeoipsExecutableCommand):
    """Config Command Class for installing packages/data.

    Supports installation of packages and test data needed for testing and/or 
    running your GeoIPS environment.
    """

    name = "install"
    command_classes = []

    def add_arguments(self):
        """Add arguments to the config-subparser for the Config Command."""
        self.parser.add_argument(
            "test_dataset_names",
            type=str.lower,
            nargs="+",
            choices=list(test_dataset_dict.keys()) + ["all"],
            help=(
                "Names of the GeoIPS test datasets to install. If 'all' is "
                "specified, GeoIPS will install all test datasets hosted on "
                "NextCloud. 'all' cannot be specified alongside other test "
                "dataset names."
            ),
        )
        
        self.parser.add_argument(
            "-o",
            "--outdir",
            type=pathlib.Path,
            default=_get_default_testdata_dir(),
            help=(
                "The full path to the directory you want to install this "
                "data to. If not provided, this command will default to "
                "$GEOIPS_TESTDATA_DIR if set else will default to the "
                "current working directory."
            ),
        )

    def __call__(self, args):
        """Run install command.

        Parameters
        ----------
        args : Namespace
            The argument namespace to parse through.
        """
        try:
            _validate_output_directory(args.outdir)
            _validate_dataset_names(args.test_dataset_names)
            
            install_datasets = _get_install_dataset_names(args.test_dataset_names)
            install_func = partial(_install_single_dataset, outdir=args.outdir)
            
            list(map(install_func, install_datasets))
            
        except (FileNotFoundError, ValueError) as e:
            self.parser.error(str(e))


class GeoipsConfigInstallGithub(GeoipsExecutableCommand):
    """Config Command Class for installing packages/data from GitHub.

    Supports installation of packages and test data needed for testing and/or 
    running your GeoIPS environment via github repositories.
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
        """Run install-github command.

        Parameters
        ----------
        args : Namespace
            The argument namespace to parse through.
        """
        print(
            f"Running check_system_requirements.sh test_data_github "
            f"{args.test_dataset_name}"
        )
        
        call_list = _build_github_install_command(args.test_dataset_name)
        subprocess.call(call_list)


class GeoipsConfig(GeoipsCommand):
    """Config top-level command for configuring your GeoIPS environment."""

    name = "config"
    command_classes = [
        GeoipsConfigInstall,
        GeoipsConfigInstallGithub,
        GeoipsConfigCreateRegistries,
        GeoipsConfigDeleteRegistries,
    ]
