# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit test for retrieving commandline instructions for the GeoIPS CLI."""

from os import listdir, remove
from os.path import dirname, exists
import pytest

from geoips.commandline.cmd_instructions import get_instructions
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
            get_instructions(ancillary_dirname=cmd_dir)
            assert exists(f"{cmd_dir}/cmd_instructions.json")
            remove(f"{cmd_dir}/cmd_instructions.json")
        else:
            with pytest.raises(FileNotFoundError):
                get_instructions(ancillary_dirname=cmd_dir)
