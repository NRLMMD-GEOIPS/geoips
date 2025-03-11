# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit tests for geoips/commandline/log_setup.py.

Tests the following functions:
- log_with_emphasis
- add_log_level (by importing geoips.logging)
"""

import pytest

import random
import string
from geoips import logging
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

    Example
    -------
    >>> insert_word_like_spaces_to_string("HelloWorld")
    'He lloW or ld'
    """
    loc = random.randint(2, 3)
    while loc < len(string):
        string = string[:loc] + " " + string[loc + 1 :]
        loc += random.randint(2, 8)
    return string


def insert_random_string_randomly(s, length):
    """Insert a randomly generated string of a given length at a random position.

    Parameters
    ----------
    s : str
        The original string into which the random string will be inserted.
    length : int
        The length of the random string to be generated and inserted.

    Returns
    -------
    str
        The modified string with a randomly generated string of length `length`
        inserted at a random position.

    Example
    --------
    >>> insert_random_string_randomly("hello", 3)
    'helXyZlo'
    """
    position = random.randint(0, len(s) - 1)
    return s[position:] + generate_random_string(length) + s[position:]


def generate_random_messages(add_long_word=False):
    """Generate a random amount of messages with random length."""
    num_messages = 20
    messages = [
        insert_word_like_spaces_to_string(
            generate_random_string(random.randint(5, 110))
        )
        for _ in range(num_messages)
    ]
    if add_long_word:

        def f(s):
            return insert_random_string_randomly(s, 88)  # insert string 88 chars long

        return list(map(f, messages))
    else:
        return messages


@pytest.mark.parametrize("message", generate_random_messages())
def test_log_with_emphasis(message, caplog, test_all_lines_same_length=True):
    """Pytest function for testing the output of 'log_with_emphasis'.

    The expected output of log_with_emphasis looks similar to this:
    ***************
    ** hello     **
    ** howdy     **
    ** what's up **
    ***************
    """  # noqa: RST212
    # ignoring check because flake8 flags the codeblocks as underlines
    caplog.set_level(logging.INFO)
    log_with_emphasis(LOG.info, message)

    assert (  # top of box is formmated correctly
        "*" * 9
        in caplog.messages[0]  # three for borders, and min of 5 for string length
    )
    assert message[0:5] in caplog.text  # test for first section of text
    assert "\n" in caplog.text  # assert log output is multi-lined

    assert caplog.messages[1].startswith("** ")  # test for left side of box
    assert caplog.messages[1].endswith(" **")  # test for left side of box

    if test_all_lines_same_length:
        assert (
            len(set(map(len, caplog.messages[:-1]))) == 1  # last line is blank
        )  # all logged lines are the same length

    with pytest.raises(ValueError):
        log_with_emphasis(LOG.info, "")


@pytest.mark.parametrize("message", generate_random_messages(add_long_word=True))
def test_log_with_emphasis_long_word(message, caplog):
    """Pytest function for testing the output of 'log_with_emphasis'.

    The expected output of log_with_emphasis usually looks like this:
    ***************
    ** hello     **
    ** howdy     **
    ** what's up **
    ***************
    However, by default we don't wrap long words. If a "long word" (string of chars
    surrounded by spaces of length >74) is present, the expected output of
    log_with_emphasis looks like this:
    ***********************************************************************************
    ** hello                                                                         **
    ** howdy                                                                         **
    ** what's up                                                                     **
    ** this is a very long string that we are not going to match at the top or bottom because it really is too long ok I think this is long enough **
    ***********************************************************************************
    """  # noqa: E501,RST212
    # ignoring line length check, and the section underline check because
    # flake8 flags the codeblocks as underlines
    caplog.set_level(logging.INFO)
    log_with_emphasis(LOG.info, message)
    log_lines = caplog.messages[1 : len(caplog.text) - 1]

    # all logged lines are NOT the same length (because we didn't wrap)
    assert not (len(set(map(len, log_lines[:-1]))) == 1)

    # find at least one line that is longer than 80 chars (aka not wrapped)
    assert any(map(lambda line: len(line) > 80, log_lines))


def test_log_interactive_geoips(caplog):
    """Test log.interactive using logging from geoips."""
    log = logging.getLogger(__name__)

    log.interactive("FROM PYTEST")
    assert "FROM PYTEST" in caplog.text
    assert "INTERACTIVE" in caplog.text


# Commenting this out, unless we can identify a test that does not require having
# test datasets cloned. Should not require test datasets to test interactive
# log from a plugin.
# def test_log_interactive_from_directly_imported_plugin(caplog):
#     """Use ABI reader, which calls log.interactive.
#
#     It used to be that plugins loaded via get_plugin outside of GeoIPS could not call
#     log.interactive. They would raise an AttributeError. This is to ensure that
#     problem has been fixed and remains fixed.
#     """
#     from geoips.interfaces import readers
#
#     reader = readers.get_plugin("abi_netcdf")
#
#     test_data_dir = os.getenv("GEOIPS_TESTDATA_DIR")
#     if test_data_dir:
#         # Only run this test if GEOIPS_TESTDATA_DIR environment variable has been set
#         # on the machine that is running the test.
#         test_data_dir += "/test_data_noaa_aws/data/goes16/20200918/1950"
#         test_data_files = glob(test_data_dir + "/*C14*.nc")
#         _ = reader(test_data_files)
#         assert "INTERACTIVE" in caplog.text
