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


def insert_word_like_spaces_to_string(string):
    """Modify the input string by inserting spaces to make "words" of length 2-8.

    Parameters
    ----------
    str (str):
        The input string to be modified.

    Returns
    -------
    str (str):
        The modified string with spaces inserted at random locations.

    Example:
    >>> insert_word_like_spaces_to_string("HelloWorld")
    'He lloW or ld'
    """
    loc = random.randint(2, 3)
    while loc < len(string):
        string = string[:loc] + " " + string[loc + 1 :]
        loc += random.randint(2, 8)
    return string


def generate_random_messages():
    """Generate a random amount of messages with random length."""
    num_messages = 20
    messages = [
        insert_word_like_spaces_to_string(
            generate_random_string(random.randint(5, 110))
        )
        for _ in range(num_messages)
    ]
    return messages


@pytest.mark.parametrize("message", generate_random_messages())
def test_log_with_emphasis(message, caplog):
    """Pytest function for testing the output of 'log_with_emphasis'."""
    caplog.set_level(logging.INFO)
    log_with_emphasis(LOG.info, message)
    assert (  # top/bottom of box is formmated correctly
        "*" * 9  # three for borders, and min of 5 for string length
    )
    assert "** " in caplog.text
    assert " **" in caplog.text
    assert message[0:5] in caplog.text
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
