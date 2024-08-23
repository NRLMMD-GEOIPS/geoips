#!/bin/env python

# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Download data from a specified URL."""
import subprocess
import requests
import tarfile
import argparse
import tempfile

try:
    from rich.console import Console
    from rich.progress import Progress

    use_rich = True
except ModuleNotFoundError as e:
    use_rich = False

try:
    from rich_argparse import RichHelpFormatter

    use_rich_formatter = True
except ModuleNotFoundError as e:
    use_rich_formatter = False

# Initialize console with a default value
console = None


def setup_rich_console(use_rich):
    global console
    console = Console() if use_rich else None


def output_to_console(message, style=None):
    if console:
        console.print(message, style=style)
    else:
        print(message)


def sizeof_fmt(num, suffix="B"):
    # from https://stackoverflow.com/a/1094933/2503170
    for unit in ("", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"):
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"


def download_from_git(repo_url, destination):
    try:
        output_to_console(
            f"Cloning repository from {repo_url} to {destination}...", style="bold cyan"
        )
        subprocess.check_output(["git", "clone", repo_url, destination])
        output_to_console("Repository successfully cloned.", style="bold green")
    except subprocess.CalledProcessError as e:
        output_to_console(
            f"Failed to clone repository: {e.output.decode('utf-8')}", style="bold red"
        )


def download_and_extract_compressed_tar(url, dest, comp="gz"):
    output_to_console(
        f"Downloading and extracting {url} to {dest}...", style="bold cyan"
    )
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            file_length = int(r.headers.get("content-length", 0))
            with tarfile.open(fileobj=r.raw, mode=f"r|{comp}") as tar:
                output_to_console(
                    f"Downloading and extracting {sizeof_fmt(file_length)}... ",
                    style="cyan",
                )
                tar.extractall(path=dest)
        output_to_console("Files successfully downloaded and extracted.", style="green")
    except Exception as e:
        output_to_console(f"Failed to download or extract files.", style="bold red")
        raise e


def main():
    global use_rich
    parser = argparse.ArgumentParser(
        description="Download test data for GeoIPS",
        formatter_class=(
            RichHelpFormatter if use_rich_formatter else argparse.HelpFormatter
        ),
    )
    parser.add_argument("url", help="The URL to the .tgz file.")
    parser.add_argument("output_dir", help="The directory to extract files to.")
    parser.add_argument(
        "--no-rich",
        action="store_true",
        help="Disable rich text formatting and progress bars.",
    )

    args = parser.parse_args()

    use_rich = not args.no_rich
    setup_rich_console(use_rich)

    if ".git" in args.url:
        download_from_git(args.url, args.output_dir)
    elif ".tgz" in args.url:
        download_and_extract_compressed_tar(args.url, args.output_dir)
    else:
        output_to_console(
            "Error: Cannot handle non-git non-tgz urls.", style="bold red"
        )


if __name__ == "__main__":
    main()
