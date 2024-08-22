#!/bin/env python

# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Download data from a specified URL."""

import sys
import urllib
import tempfile
from subprocess import check_output
import urllib.request


def download_test_data(url, dest=None):
    """Download the specified URL and write to stdout as bytes.

    Will raise requests.exceptions.HTTPError on failure.
    """
    if ".git" in url:
        print(f"git clone {url} {dest}")
        check_output(["git", "clone", url, dest])
        print("done git clone")
    else:
        with tempfile.NamedTemporaryFile(delete_on_close=False) as f:
            with urllib.request.urlopen(url) as url_stream:
                urllib.request.urlretrieve(url_stream, f)
            print(f.name)


if __name__ == "__main__":
    dest = None
    if len(sys.argv) == 3:
        dest = sys.argv[2]
    download_test_data(sys.argv[1], dest)
