# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit test for retrieving commandline instructions for the GeoIPS CLI."""

import os
from os.path import dirname, exists

import pytest
import tempfile

from geoips.utils.cache_files import get_cached_json
from geoips.commandline.commandline_interface import GeoipsCLI


# This points to the instructions directory for the unit tests. These are test
# instructions that are not used in the actual codebase.
INSTRUCT_DIR = f"{str(dirname(__file__))}/cmd_instructions"


def generate_id(dir_name):
    """Generate a test id for the instructions directory being tested."""
    return dir_name


@pytest.mark.parametrize("dir_name", os.listdir(INSTRUCT_DIR), ids=generate_id)
def test_instruction_cases(dir_name):
    """Check that the instructions found in dir_name pass or raise the correct error.

    Parameters
    ----------
    dir_name: str
        - The directory name containing the cmd_instructions we want to test
        - Will be testing:
            - missing both .yaml and .json instructions
            - missing .json instructions
            - missing .yaml instructions
            - invalid .json instructions
            - invalid .yaml instructions
            - newer .yaml file than the .json file
            - newer .json file than the .yaml file
    """
    # This will take the place of the user cache directory for the unit tests.
    # This is where the cached JSON files will be stored.
    # This is a temporary directory that will be deleted when the test is complete.
    cache_dir = tempfile.mkdtemp()

    # Path to the directory containing the YAML instructions
    cmd_dir = f"{INSTRUCT_DIR}/{dir_name}"
    cmd_yaml = f"{cmd_dir}/cmd_instructions.yaml"
    cmd_json = f"{cache_dir}/cmd_instructions.json"

    if "invalid" in dir_name:
        # Load the invalid instructions
        cmd_instructions = get_cached_json(
            f"{cmd_dir}/cmd_instructions.yaml",
            cache_dir=cache_dir,
        )
        # Ensure that a key error is raised
        GeoipsCLI(cmd_instructions=cmd_instructions)
    elif "missing" in dir_name:
        if dir_name == "json_missing":
            cmd_instructions = get_cached_json(cmd_yaml, cache_dir=cache_dir)
            assert exists(cmd_json)
        else:
            with pytest.raises(FileNotFoundError):
                get_cached_json(cmd_yaml, cache_dir=cache_dir)

    # Clean up
    try:
        os.remove(cmd_json)
    except FileNotFoundError:
        pass
    os.rmdir(cache_dir)
