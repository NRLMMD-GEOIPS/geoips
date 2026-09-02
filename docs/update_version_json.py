# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Conditionally updates the pydata-sphinx-theme version switcher json file.

TODO: rework to be compatabile with both old and new approaches
"""

import argparse
import json
from pathlib import Path
from typing import List, Dict

BASE_URL = "https://nrlmmd-geoips.github.io/geoips/"
BASE_VERSION_CONFIG = [
    {
        "version": "stable",
        "url": f"{BASE_URL}stable/",
        "is_latest": true
    },
    {
        "version": "dev",
        "url": f"{BASE_URL}dev/"
    },
]

def get_version_list(filepath: Path) -> List[Dict]:
    """Open json file and return list if it passes validation."""
    with filepath.open() as f:
        output = json.load(f)
    if (
        type(output) != list
        or len(output) < 3
        or "version" not in output[0]
        or "url" not in output[0]
    ):
        raise ValueError("Invalid version JSON file specified")
    return output


def update_version_list(filepath: Path, name: str, current_list: List):
    """Update version json, inserting as new 3rd element behind stable and dev."""
    this_version_dict = {"url": f"{BASE_URL}{name}/"}
    if name.startswith("v"):
        this_version_dict["name"] = name
        this_version_dict["version"] = name[1:]
    else:
        this_version_dict["version"] = name
    new_version_list = current_list.append(this_version_dict)
    with filepath.open("w") as f:
        json.dump(new_version_list, f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Conditionally update pydata-sphinx-theme version switcher json"
    )

    parser.add_argument(
        "-n",
        "--name",
        type=str,
        help="Name of version"
    )
    parser.add_argument(
        "-f",
        "--file",
        type=Path,
        help="Path to json version file"
    )

    args = parser.parse_args()
    version_list = get_version_list(args.file)
    versions_present = [item["version"] for item in version_list]
    if args.name not in versions_present:
        update_version_list(args.file, args.name, version_list)
        print(f"Version {args.name} added to version json.")
    else:
        print(f"Version {args.name} already present in version json, no need to update.")
