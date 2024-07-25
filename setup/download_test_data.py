#!/bin/env python

# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

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
