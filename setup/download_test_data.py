#!/bin/env python

# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Download data from a specified URL."""
import subprocess
import requests
import tarfile
import argparse
import os

import yaml


def get_argparse_formatter():
    """
    Determine and return the appropriate argument parser help formatter.

    Tries to import ``RichHelpFormatter`` from the ``rich_argparse`` package. If the
    import fails, it defaults to using the argparse default: ``argparse.HelpFormatter``.

    Returns
    -------
    argparse.HelpFormatter or rich_argparse.RichHelpFormatter
        The formatter class to use for argument parsing help messages.
    """
    try:
        from rich_argparse import RichHelpFormatter

        return RichHelpFormatter
    except ModuleNotFoundError:
        return argparse.HelpFormatter


def setup_rich_console(use_rich):
    """
    Set up global ``output_to_console`` function using `rich` if available.

    Sets global variable ``output_to_console`` to a function that handles
    styled output using ``rich`` if ``use_rich`` is True and ``rich`` is installed,
    otherwise falls back to using standard print function.

    Parameters
    ----------
    use_rich : bool
        If True, attempts to use the `rich` library for styled console output.

    Returns
    -------
    None

    Global Variables
    ----------------
    output_to_console : function
        A function to handle console output, with or without styling.
    """
    global output_to_console
    if use_rich:
        try:
            from rich.console import Console

            con = Console()

            def output_to_console(msg, style):
                con.print(msg, style=style)

            return
        except ModuleNotFoundError:
            pass

    def output_to_console(msg, style):
        print(msg)


def sizeof_fmt(num, suffix="B"):
    """
    Convert a byte size into a human-readable string (eg. MiB).

    Parameters
    ----------
    num : int
        The size in bytes to convert.
    suffix : str, optional
        The suffix to append to the size (default is "B" for bytes).

    Returns
    -------
    str
        The size converted into a human-readable string with appropriate units.

    Notes
    -----
    This function is adapted from: https://stackoverflow.com/a/1094933/2503170
    """
    for unit in ("", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"):
        if abs(num) < 1024.0:
            return f"{num:3.1f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"


def download_from_git(repo_url, destination):
    """
    Clone a git repository from the specified URL to given destination.

    Parameters
    ----------
    repo_url : str
        The URL of the git repository to clone.
    destination : str
        The local directory where the repository should be cloned.

    Return
    -------
    None

    Raises
    ------
    subprocess.CalledProcessError
        If the git clone command fails.
    """
    try:
        output_to_console(
            f"Cloning repository from {repo_url} to {destination}",
            style="bold cyan",
        )
        subprocess.check_output(["git", "clone", repo_url, destination])
        output_to_console("Repository successfully cloned.", style="bold green")
    except subprocess.CalledProcessError as e:
        output_to_console(
            f"Failed to clone repository: {e.output.decode('utf-8')}", style="bold red"
        )
        raise e


def download_and_extract_compressed_tar(url, dest, comp="gz"):
    """
    Download a compressed tar file from a URL and extract its contents.

    This function streams the download of a compressed tar file,
    supporting various compression types (e.g., gzip by default),
    and extracts the files directly to the specified destination directory.
    It does this in memory in chunks to prevent a memory overflow on large files and
    for a speed increase by never having to re-read data off of slower non-RAM memory.

    Parameters
    ----------
    url : str
        The URL of the compressed tar file to download
    dest : str
        The directory where the contents of the tar file should be extracted.
        If the directory does not exist,
        it should be created prior to calling this function.
    comp : str, optional
        The compression type used in the tar file. Accepted values include:
        - "gz" for gzip compression (default).
        - "bz2" for bzip2 compression.
        - "xz" for xz compression.
        This parameter determines how the tar file will be read and decompressed.

    Returns
    -------
    None
    """
    output_to_console(
        f"Downloading and extracting {url} to {dest}...", style="bold cyan"
    )
    try:
        with requests.get(url, stream=True, timeout=360) as r:
            r.raise_for_status()
            file_length = int(r.headers.get("content-length", 0))
            with tarfile.open(fileobj=r.raw, mode=f"r|{comp}") as tar:
                output_to_console(
                    f"File is {sizeof_fmt(file_length)}... ",
                    style="cyan",
                )
                # Trusting archives to not be malicious by not filtering files
                # tar.extractall(path=dest)  # nosec
                for item_to_extract in tar:
                    if not os.path.abspath(
                        os.path.join(dest, item_to_extract.name)
                    ).startswith(dest):
                        raise SystemExit(f"Found unsafe filepath in tar from url {url}")
                    elif (
                        os.path.isabs(item_to_extract.name)
                        or ".." in item_to_extract.name
                    ):
                        raise ValueError("Illegal tar archive entry from url {url}")
                    tar.extract(item_to_extract, path=dest)

        output_to_console("Success. Files downloaded and extracted.", style="green")
    except Exception as e:
        output_to_console("Failed to download or extract files.", style="bold red")
        raise e


def get_test_data_urls():
    """
    Retrieve test data URLs from a YAML configuration file.

    This function reads a YAML file named `test-data-urls.yaml` located
    in the same directory as the script and returns the URLs specified
    under the `test_data_urls` key.

    Returns
    -------
    list of str
        A list of test data URLs.

    Examples
    --------
    >>> urls = get_test_data_urls()
    >>> print(urls)
    ['https://example.com/data1.csv', 'https://example.com/data2.csv']
    """
    dirname, filename = os.path.split(os.path.abspath(__file__))
    with open(os.path.join(dirname, "test-data-urls.yaml"), "r") as f:
        data = yaml.safe_load(f)
        return data["test_data_urls"]


def main():
    """
    Handle command-line arguments and initiate the download process.

    Determines what function to call based off of input value.
    Also configures the console output style based on user preferences.

    Returns
    -------
    None
    """
    parser = argparse.ArgumentParser(
        description="Download test data for GeoIPS",
        formatter_class=get_argparse_formatter(),
    )
    parser.add_argument(
        "input",
        help="The test data set to download, URL to the .tgz file or URL to git repo.",
        nargs="?",
        default=None,
    )
    parser.add_argument(
        "--output-dir",
        help="The directory to extract/clone files to.",
        default=None,
    )
    parser.add_argument(
        "--no-rich",
        action="store_true",
        help="Disable rich text formatting and progress bars.",
    )
    parser.add_argument(
        "--test-data-available",
        action="store_true",
        help="Returns 0 if available, else 1.",
    )
    parser.add_argument(
        "--list-test-datasets",
        action="store_true",
        default=False,
        help="List test data sets available for download.",
        required=False,
    )

    args = parser.parse_args()

    use_rich = not args.no_rich
    setup_rich_console(use_rich)

    test_data_urls = get_test_data_urls()
    if args.test_data_available:
        if args.input is None:
            raise argparse.ArgumentError("Please pass a test data set")
        if args.input in test_data_urls.keys():
            output_to_console(
                f"{args.input} is available for direct download.", style="green"
            )
            exit()
        else:
            output_to_console(
                f"{args.input} is NOT available for direct download.", style="red"
            )
            exit(1)
    if args.list_test_datasets:
        output_to_console("Available data sets:\n", style="")
        for key in test_data_urls.keys():
            output_to_console(f"\t{key}", style="cyan")
        exit()

    if not (args.input and args.output_dir):
        output_to_console("Invalid arguments.", style="bold red")
        parser.print_help()
        exit(1)

    if args.input in test_data_urls.keys():
        output_to_console(f"Recognized test data set [{args.input}]", style="cyan")
        url = test_data_urls[args.input]
        output_to_console(f"Trying to download from url {url}", style="cyan")
    else:
        url = args.input

    if ".git" in url:
        download_from_git(url, args.output_dir)
    elif ".tgz" in url:
        download_and_extract_compressed_tar(url, args.output_dir)
    else:
        output_to_console(
            "Error: Cannot handle non-git non-tgz urls.", style="bold red"
        )


if __name__ == "__main__":
    main()
