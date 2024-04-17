"""Unit test for retrieving commandline instructions for the GeoIPS CLI."""

from os import listdir, remove
from os.path import dirname, exists
import pytest

from geoips.commandline.ancillary_info import (
    get_cmd_instructions,
    cmd_instructions_modified,
)
from geoips.commandline.commandline_interface import GeoipsCLI


instruct_dir = f"{str(dirname(__file__))}/cmd_instructions"


def generate_id(dir_name):
    """Generate a test id for the instructions directory being tested."""
    return dir_name


@pytest.mark.parametrize("dir_name", listdir(instruct_dir), ids=generate_id)
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
    cmd_dir = f"{instruct_dir}/{dir_name}"
    if "invalid" in dir_name:
        # Ensure that a key error is raised
        with pytest.raises(KeyError):
            GeoipsCLI(instructions_dir=cmd_dir)
    elif "missing" in dir_name:
        if dir_name == "json_missing":
            get_cmd_instructions(ancillary_dirname=cmd_dir)
            assert exists(f"{cmd_dir}/cmd_instructions.json")
            remove(f"{cmd_dir}/cmd_instructions.json")
        else:
            with pytest.raises(FileNotFoundError):
                get_cmd_instructions(ancillary_dirname=cmd_dir)
    elif "newer" in dir_name:
        yaml_newer = cmd_instructions_modified(ancillary_dirname=cmd_dir)
        # we are not using get_cmd_instructions here as this would overwrite the json
        # instructions and this test case would be in the incorrect state. This function
        # would still be called though and ensures that coverage passes
        if dir_name == "json_newer":
            assert yaml_newer == False
        else:
            assert yaml_newer == True
