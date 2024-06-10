"""
This generates release notes from YAML files and writes them to an output .rst file.
"""

import argparse
import os
import rich.progress
import yaml
from datetime import datetime

import pygit2
from rich.console import Console

console = Console()


default_categories = [
    "bug-fix",
    "feature",
    "enhancement",
    "deprecation",
    "removal",
    "security",
    "performance",
    "documentation",
    "maintenance",
    "other",
]

default_title = "NO TITLE"
default_description = "NO DESCRIPTION"


def parse_arguments():
    """
    Parse command line arguments for input folder and output file.

    Returns
    -------
    argparse.Namespace
        Parsed arguments containing input_folder and output_file.
    """
    parser = argparse.ArgumentParser(
        description="Generate release notes from YAML files."
    )
    parser.add_argument(
        "-t",
        "--write-yaml-template",
        type=str,
        help="Write template YAML to provided file."
        + " If folder provided, place template in folder with current "
        + "git branch name as file name.",
        nargs="?",
        default=argparse.SUPPRESS,
    )
    parser.add_argument(
        "input_files_or_folders",
        type=str,
        nargs="*",
        help="The folder(s) containing YAML files and/or YAML files. "
        + "Folders will be searched recursively.",
    )
    parser.add_argument(
        "-v",
        "--version",
        type=str,
        default="[UNKNOWN]",
        help="Version number of the release. Default is '[UNKNOWN]'.",
        required=False,
    )

    parser.add_argument(
        "-head",
        "--header_file",
        type=str,
        help="A header file to prepend to the release notes.",
    )
    parser.add_argument(
        "-o", "--output_file", type=str, help="The output file for release notes."
    )
    return parser.parse_args(), parser


def exit_on_invalid_arguments(args, parser):
    """
    Validate the argparse arguments.

    This function validates the provided argparse arguments to ensure
    that the required input files/folders and output file are provided.
    If arguments are invalid, it prints an error message and exits the program.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed arguments.

    parser : argparse.ArgumentParser
        The ArgumentParser object used to parse the command-line arguments.
    """
    if bool(args.output_file) == bool(args.input_files_or_folders):
        return

    if "write_yaml_template" in args:
        if args.write_yaml_template is not None:
            return

    console.print("[bold red]Invalid arguments.\n")
    parser.print_help()
    exit(1)


def get_yaml_template_path(file_path_arg):
    if file_path_arg is None:
        filepath = os.getcwd()
        filename = f"{get_current_git_branch()}.yaml"
        return os.path.join(filepath, filename)
    if not file_path_arg.endswith(".yaml"):
        return file_path_arg + ".yaml"
    return file_path_arg


def create_blank_template_yaml_file(file_path_arg):
    """
    Create a blank YAML file with default categories.

    Parameters
    ----------
    file_path : str
        Path to the output YAML file.
    """
    default_yaml = {
        category: [{"title": "", "description": ""}] for category in default_categories
    }
    yaml_template_path = get_yaml_template_path(file_path_arg)
    with open(yaml_template_path, "w") as file:
        yaml.dump(default_yaml, file)


def find_duplicate_titles(data):
    """
    Check if there are any duplicate titles in dictionaries of lists of dictionaries.

    Args:
        data (dict): A dictionary containing lists of dictionaries with items
         indexed by "title".

    Returns:
        bool: True if there are duplicate "title" values, False otherwise.
    """
    titles = [entry["title"] for category in data for entry in data[category]]
    return not len(set(titles)) == len(titles)


def exit_on_invalid_yaml(content, file_path):
    """
    Check if the YAML content follows the correct schema.

    Parameters
    ----------
    content : dict
        Parsed content of the YAML file.
    file_path : str
        Path to the YAML file.

    Raises
    ------
    ValueError
        If the YAML content does not follow the correct schema.
    """
    for category, entries in content.items():
        if not isinstance(entries, list):
            raise ValueError(
                f"Invalid YAML content in file {file_path}. "
                + "Entries for category '{category}' must be a list."
            )

        for entry in entries:
            if not isinstance(entry, dict):
                raise ValueError(
                    f"Invalid YAML content in file {file_path}. "
                    + "Entry in category '{category}' must be a dictionary."
                )
            if not set(entry.keys()) == {"title", "description"}:
                raise ValueError(
                    f"Invalid YAML content in file {file_path}. "
                    + "Entry in category '{category}' must only have "
                    + "'title' and 'description' keys."
                )


def read_yaml_files(input_files):
    """
    Read and parse the given list of YAML files.

    Parameters
    ----------
    input_files : list
        List of paths to the YAML files.

    Returns
    -------
    dict
        Parsed content of all YAML files categorized by type of change.

    Examples
    --------
    >>> read_yaml_files(["file1.yaml", "file2.yaml"])
    {'bug-fix': [
        {'title': 'fixed explosions',
          'description': 'This fixed the explosion mechanism'},
        {'title': 'fixed cats not being cute',
          'description': 'This made the cats WAY cuter'}
        ]
    }
    """
    data = {}
    for file_path in input_files:
        with rich.progress.open(
            file_path, "r", description=f"Reading {file_path}"
        ) as file:
            content = yaml.safe_load(file)
            exit_on_invalid_yaml(content, file_path)
            for category, entries in content.items():
                entries = [
                    entry
                    for entry in entries
                    if not (entry["title"] == "" and entry["description"] == "")
                ]
                if category not in data and len(entries) > 0:
                    data[category] = []
                if len(entries) > 0:
                    data[category].extend(entries)
    return data


def format_release_notes(data, version, release_date=None):
    """
    Format the parsed YAML data into release notes in .rst format.

    Parameters
    ----------
    data : dict
        Parsed content of YAML files.
    version : str, optional
        Version number of the release, by default '1.1'.
    release_date : str, optional
        Release date, by default None, which uses today's date.

    Returns
    -------
    str
        Formatted release notes in .rst format.
    """
    if release_date is None:
        release_date = datetime.now().strftime("%Y-%m-%d")

    header = f"Version {version} ({release_date})\n"
    header = header + ("*" * (len(header) - 1)) + ("\n" * 2)
    summary = ""
    detailed = ""

    for category, entries in data.items():
        detailed += f"{category.capitalize()}\n" + "=" * len(category) + "\n\n"
        for entry in entries:
            title = entry["title"]
            description = entry["description"]
            if title == "":
                title = default_title
            if description == "":
                description = default_description

            summary += f" * *{category.capitalize()}*: {title}\n"

            detailed += f"{title}\n" + "-" * len(title) + "\n\n"
            detailed += f"{description}\n\n"

    return header + summary + "\n" + detailed[:-1]


def get_yaml_files_from_input(input_files_or_folders):
    """
    Get a list of YAML files from the given input files or folders.

    Parameters
    ----------
    input_files_or_folders : list
        List of paths to input files or folders.

    Returns
    -------
    list
        List of paths to YAML files.

    Raises
    ------
    ValueError
        If a file is not a YAML file or if no YAML files are found in a directory.
    """
    yaml_files = []
    for path in input_files_or_folders:
        if os.path.isfile(path):
            if not path.endswith(".yaml"):
                raise ValueError(f"File {path} is not a YAML file.")
            yaml_files.append(path)
        elif os.path.isdir(path):
            dir_yaml_files = []
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.endswith(".yaml"):
                        dir_yaml_files.append(os.path.join(root, file))
            if len(dir_yaml_files) == 0:
                raise ValueError(f"No YAML files found in directory {path}.")
            yaml_files.extend(dir_yaml_files)
        else:
            console.print(f"[red]Invalid file or directory: [bold]{path}[/]")
            exit(1)
    return yaml_files


def write_output_file(output_file, content):
    """
    Write the formatted release notes to the output file.

    Parameters
    ----------
    output_file : str
        Path to the output .rst file.
    content : str
        Formatted release notes.
    """
    with open(output_file, "w") as file:
        file.write(content)
        console.print(f"[green]Wrote release notes to {output_file}")


def get_current_git_branch():
    """
    Get the current git branch name.

    Returns
    -------
    str
        The name of the current git branch.
    """
    try:
        repo = pygit2.Repository(".")
    except pygit2.GitError:
        console.print(
            "[bold red]Could not find a git repo. Please run in a "
            + "git repo or pass a file path for the yaml template "
            + "(eg '-t /path/to/file.yaml')."
        )
        exit(1)
    return repo.head.shorthand


def main():
    """
    Main function to generate release notes from YAML files and write to an output file.
    """
    args, parser = parse_arguments()
    exit_on_invalid_arguments(args, parser)
    if "write_yaml_template" in args:
        create_blank_template_yaml_file(args.write_yaml_template)
    if args.input_files_or_folders:
        yaml_files = get_yaml_files_from_input(args.input_files_or_folders)
        data = read_yaml_files(yaml_files)
        content = format_release_notes(data, version=args.version)
        if args.header_file:
            with rich.progress.open(
                args.header_file, "r", description=f"Reading {args.header_file}"
            ) as file:
                header = file.read()
                content = header + "\n" + content
        write_output_file(args.output_file, content)


if __name__ == "__main__":
    main()
