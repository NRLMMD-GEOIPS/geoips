"""Unit tests for geoips/commandline/log_setup.py.

Tests the following functions:
- log_with_emphasis
- add_log_level (by importing geoips.logging)
"""

import pytest

import os
import random
import string
from geoips import logging
from glob import glob
from geoips.commandline.log_setup import log_with_emphasis

LOG = logging.getLogger(__name__)


def generate_random_string(length):
    """Generate a random string of length :param length."""
    return "".join(random.choices(string.ascii_letters, k=length))


def generate_random_messages():
    """Generate a random amount of messages with random length."""
    num_messages = random.randint(1, 50)
    return [generate_random_string(random.randint(5, 110)) for _ in range(num_messages)]


@pytest.mark.parametrize("message", generate_random_messages())
def test_log_with_emphasis(message, caplog):
    """Pytest function for testing the output of 'log_with_emphasis'."""
    caplog.set_level(logging.INFO)
    max_message_len = min(80, len(message)) + 6
    assert max_message_len <= 86, "Max emphasis in '*' is longer than 80 chars."
    log_with_emphasis(LOG.info, message)
    assert "*" * max_message_len in caplog.text
    assert "** " + message in caplog.text
    assert "*" * max_message_len in caplog.text
    assert "\n" in caplog.text


def test_log_interactive_geoips(caplog):
    """Test log.interactive using logging from geoips."""
    log = logging.getLogger(__name__)

    log.interactive("FROM PYTEST")
    assert "FROM PYTEST" in caplog.text
    assert "INTERACTIVE" in caplog.text


def test_log_interactive_from_directly_imported_plugin(caplog):
    """Use ABI reader, which calls log.interactive.

    It used to be that plugins loaded via get_plugin outside of GeoIPS could not call
    log.interactive. They would raise an AttributeError. This is to ensure that problem
    has been fixed and remains fixed.
    """
    from geoips.interfaces import readers

    reader = readers.get_plugin("abi_netcdf")

    test_data_dir = os.getenv("GEOIPS_TESTDATA_DIR")
    test_data_dir += "/test_data_noaa_aws/data/goes16/20200918/1950"
    test_data_files = glob(test_data_dir + "/*C14*.nc")
    _ = reader(test_data_files)
    assert "INTERACTIVE" in caplog.text
