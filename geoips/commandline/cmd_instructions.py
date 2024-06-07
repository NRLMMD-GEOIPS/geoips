# # # Distribution Statement A. Approved for public release. Distribution unlimited.
# # #
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # #
# # # This program is free software: you can redistribute it and/or modify it under
# # # the terms of the NRLMMD License included with this program. This program is
# # # distributed WITHOUT ANY WARRANTY; without even the implied warranty of
# # # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the included license
# # # for more details. If you did not receive the license, for more information see:
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/

"""Module for retrieving help information for the GeoIPS Command Line Interface.

Used to dynamically load and apply help information to all 'geoips' commands.
"""

import json
from os.path import dirname, exists, getmtime
import yaml


def cmd_instructions_modified(ancillary_dirname):
    """Check whether or not cmd_instructions.yaml has been modified.

    This uses os.path.getmtime(fname) determine whether or not the YAML command help
    instructions have been modified more recently than when we last generated our JSON
    instructions file. Return the truth value to whether or not cmd_instructions.yaml
    has been modified more recently than cmd_instructions.json

    Parameters
    ----------
    ancillary_dirname: str
        - The path to the folder which contains the help instructions for the CLI

    Returns
    -------
    yaml_recently_modified: bool
        - The truth value as to whether or not the yaml cmd_instructions were modified
          more recently than the json cmd_instructions
    """
    json_mtime = getmtime(f"{ancillary_dirname}/cmd_instructions.json")
    yaml_mtime = getmtime(f"{ancillary_dirname}/cmd_instructions.yaml")
    yaml_recently_modified = False
    if yaml_mtime > json_mtime:
        # yaml file was modified more recently than json_mtime
        yaml_recently_modified = True
    return yaml_recently_modified


def get_cmd_instructions(ancillary_dirname=None):
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

    Returns
    -------
    cmd_instructions: dict
        - Dictionary of help instructions for every CLI command
    """
    if ancillary_dirname is None or not isinstance(ancillary_dirname, str):
        # use the default command instructions
        ancillary_dirname = str(dirname(__file__)) + "/ancillary_info"
    if not exists(f"{ancillary_dirname}/cmd_instructions.yaml"):
        err_str = f"File {ancillary_dirname}/cmd_instructions.yaml is missing, please "
        err_str += "create that file at the specified location in order to use the CLI."
        raise FileNotFoundError(err_str)
    if not exists(
        f"{ancillary_dirname}/cmd_instructions.json"
    ) or cmd_instructions_modified(ancillary_dirname):
        # JSON Command Instructions don't exist yet or yaml instructions were recently
        # modified; load in the YAML Command Instructions and dump those to a JSON File,
        # but just assign the instructions to what we loaded from the yaml file since
        # they already exist in memory
        with open(
            f"{ancillary_dirname}/cmd_instructions.yaml",
            "r",
        ) as yml_instruct, open(
            f"{ancillary_dirname}/cmd_instructions.json",
            "w",
        ) as jfile:
            cmd_yaml = yaml.safe_load(yml_instruct)
            json.dump(cmd_yaml, jfile, indent=4)
            cmd_instructions = cmd_yaml
    else:
        # Otherwise load in the JSON file as it's much quicker.
        cmd_instructions = json.load(
            open(f"{ancillary_dirname}/cmd_instructions.json", "r")
        )
    return cmd_instructions


cmd_instructions = get_cmd_instructions()
