#!/bin/env python

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
