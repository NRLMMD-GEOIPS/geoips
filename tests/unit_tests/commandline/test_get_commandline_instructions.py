# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit test for retrieving commandline instructions for the GeoIPS CLI."""

from datetime import datetime, timezone
from os import listdir, remove
from os.path import dirname, exists
import pytest
import yaml

from geoips.commandline.cmd_instructions import get_instructions, instructions_modified
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
    elif "newer" in dir_name:
        yaml_newer = instructions_modified(ancillary_dirname=cmd_dir)
        # we are not using get_cmd_instructions here as this would overwrite the json
        # instructions and this test case would be in the incorrect state. This function
        # would still be called though and ensures that coverage passes

        # NOTE: The nested if statements are needed for errors that occur from git. When
        # pulling from our remote repo, we download these files at the same time and
        # they are out of sync. Since this is an extreme corner case, just modify the
        # file, rerun cmd_instructions_modified, then assert that yaml newer is True.

        if dir_name == "json_newer":
            if yaml_newer == True:
                get_instructions(ancillary_dirname=cmd_dir)
                yaml_newer = instructions_modified(ancillary_dirname=cmd_dir)
            assert yaml_newer == False
        else:
            if yaml_newer == False:
                fpath = f"{cmd_dir}/cmd_instructions.yaml"
                cmd_yaml = yaml.safe_load(open(fpath, "r"))
                write_time = datetime.now(timezone.utc)
                current_time_str = write_time.strftime("%Y-%m-%d_%H:%M:%S_%Z")
                # replace 'name' with the current time so the yaml file is more
                # recently modified.
                cmd_yaml["name"] = current_time_str
                with open(fpath, "w") as f:
                    yaml.safe_dump(cmd_yaml, f)
                yaml_newer = instructions_modified(ancillary_dirname=cmd_dir)
            assert yaml_newer == True
