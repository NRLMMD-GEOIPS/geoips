# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""geoips.commandline.ancillary_info init file."""
import os
from geoips.utils.cache_files import get_cached_json


# This will collect ancillary information contained in YAML files, but will convert them
# to a cached JSON file first. This is done because reading YAML files is slow.
alias_mapping = get_cached_json(f"{os.path.dirname(__file__)}/alias_mapping.yaml")
cmd_instructions = get_cached_json(f"{os.path.dirname(__file__)}/cmd_instructions.yaml")
