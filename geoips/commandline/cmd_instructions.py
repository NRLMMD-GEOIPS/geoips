# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Module for retrieving help information for the GeoIPS Command Line Interface.

Used to dynamically load and apply help information to all 'geoips' commands.
"""

import json
from os.path import dirname, exists, getmtime
import yaml


def instructions_modified(ancillary_dirname, fname="cmd_instructions.yaml"):
    """Check whether or not {fname}.yaml has been modified.

    This uses os.path.getmtime(fname) determine whether or not the YAML command help
    instructions have been modified more recently than when we last generated our JSON
    instructions file. Return the truth value to whether or not cmd_instructions.yaml
    has been modified more recently than cmd_instructions.json

    Parameters
    ----------
    ancillary_dirname: str
        - The path to the folder which contains the help instructions for the CLI
    fname: str (optional)
        - The name of the file that we will be checking the modification
          time of.

    Returns
    -------
    yaml_recently_modified: bool
        - The truth value as to whether or not the yaml cmd_instructions were modified
          more recently than the json cmd_instructions
    """
    json_mtime = getmtime(f"{ancillary_dirname}/{fname.replace('yaml', 'json')}")
    yaml_mtime = getmtime(f"{ancillary_dirname}/{fname}")
    yaml_recently_modified = False
    if yaml_mtime >= json_mtime:
        # yaml file was modified more recently than json_mtime
        yaml_recently_modified = True
    return yaml_recently_modified


def get_instructions(ancillary_dirname=None, fname="cmd_instructions.yaml"):
    """Return a dictionary of instructions for each command, obtained by a yaml file.

    This has been placed as a module attribute so we don't perform this process for
    every CLI command. It was taking too long to initialize the CLI and this was a
    large partof that. See
    https://github.com/NRLMMD-GEOIPS/geoips/pull/444#discussion_r1541864672 for more
    information.

    For more information on what's available, see:
        geoips/commandline/ancillary_info/cmd_instructions.yaml

    Parameters
    ----------
    ancillary_dirname: str
        - The path to the folder which contains the help instructions for the CLI.
          Defaults to None in case a user wants to supply a different path for testing
          purposes
    fname: str (optional)
        - The name of the file that we will be checking the modification
          time of.

    Returns
    -------
    cmd_instructions: dict
        - Dictionary of help instructions for every CLI command
    """
    if ancillary_dirname is None or not isinstance(ancillary_dirname, str):
        # use the default command instructions
        ancillary_dirname = str(dirname(__file__)) + "/ancillary_info"
    if not exists(f"{ancillary_dirname}/{fname}"):
        err_str = f"File {ancillary_dirname}/{fname} is missing, please "
        err_str += "create that file at the specified location in order to use the CLI."
        raise FileNotFoundError(err_str)
    if not exists(
        f"{ancillary_dirname}/{fname.replace('yaml', 'json')}"
    ) or instructions_modified(ancillary_dirname, fname):
        # JSON Command Instructions don't exist yet or yaml instructions were recently
        # modified; load in the YAML Command Instructions and dump those to a JSON File,
        # but just assign the instructions to what we loaded from the yaml file since
        # they already exist in memory
        with open(
            f"{ancillary_dirname}/{fname}",
            "r",
        ) as yml_instruct, open(
            f"{ancillary_dirname}/{fname.replace('yaml', 'json')}",
            "w",
        ) as jfile:
            yaml_file = yaml.safe_load(yml_instruct)
            json.dump(yaml_file, jfile, indent=4)
            instructions = yaml_file
    else:
        # Otherwise load in the JSON file as it's much quicker.
        instructions = json.load(
            open(f"{ancillary_dirname}/{fname.replace('yaml', 'json')}", "r")
        )
    return instructions


cmd_instructions = get_instructions()
alias_mapping = get_instructions(fname="alias_mapping.yaml")
