#!/bin/env python

# # # Distribution Statement A. Approved for public release. Distribution is unlimited.
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

"""Download data from a specified URL."""

import sys
import requests
from subprocess import check_output


def download_test_data(url, dest=None):
    """Download the specified URL and write to stdout as bytes.

    Will raise requests.exceptions.HTTPError on failure.
    """
    if ".git" in url:
        print(f"git clone {url} {dest}")
        check_output(["git", "clone", url, dest])
        print("done git clone")
    else:
        resp = requests.get(url, stream=True, timeout=15)
        sys.stdout.buffer.write(resp.raw.read())


if __name__ == "__main__":
    dest = None
    if len(sys.argv) == 3:
        dest = sys.argv[2]
    download_test_data(sys.argv[1], dest)
