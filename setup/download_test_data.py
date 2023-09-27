#!/bin/env python

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

"""Download data from a specified URL."""

import sys
import requests


def download_test_data(url):
    """Download the specified URL and write to stdout as bytes.

    Will raise requests.exceptions.HTTPError on failure.
    """
    resp = requests.get(url, stream=True, timeout=15)
    sys.stdout.buffer.write(resp.raw.read())


if __name__ == "__main__":
    download_test_data(sys.argv[1])
