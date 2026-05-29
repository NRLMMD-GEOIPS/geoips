# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit tests for geoips/commandline/log_setup.py.

Tests the following functions:
- log_with_emphasis
- add_log_level (by importing geoips.logging)
"""

import random
import string

import pytest

from geoips import logging
from geoips.commandline.log_setup import log_with_emphasis

LOG = logging.getLogger(__name__)
NUM_RANDOM_MESSAGES = 20


def generate_random_string(rng, length):
    """Generate a random string of length :param length."""
    return "".join(rng.choices(string.ascii_letters, k=length))


def insert_word_like_spaces_to_string(rng, value):
    """Modify the input string by inserting spaces to make "words" of length 2-8.

    Parameters
    ----------
    value : str
        The input string to be modified.

    Returns
    -------
    str
        The modified string with spaces inserted at random locations.

    Example
    -------
    >>> rng = random.Random(0)
    >>> insert_word_like_spaces_to_string(rng, "HelloWorld")
    'Hel oWo ld'
    """
    loc = rng.randint(2, 3)
    while loc < len(value):
        value = value[:loc] + " " + value[loc + 1 :]
        loc += rng.randint(2, 8)
    return value


def insert_random_string_randomly(rng, value, length):
    """Insert a randomly generated string of a given length at a random position.

    Parameters
    ----------
    value : str
        The original string into which the random string will be inserted.
    length : int
        The length of the random string to be generated and inserted.

    Returns
    -------
    str
        The modified string with a randomly generated string of length `length`
        inserted at a random position.
    """
    position = rng.randint(0, len(value) - 1)
    return value[:position] + generate_random_string(rng, length) + value[position:]


def generate_random_message(seed, add_long_word=False):
    """Generate one deterministic random message from a seed."""
    rng = random.Random(seed)

    message = insert_word_like_spaces_to_string(
        rng,
        generate_random_string(rng, rng.randint(5, 110)),
    )

    if add_long_word:
        message = insert_random_string_randomly(
            rng, message, 88
        )  # insert string 88 chars long

    return message


@pytest.mark.parametrize(
    "seed",
    range(NUM_RANDOM_MESSAGES),
    ids=lambda seed: f"seed-{seed}",
)
def test_log_with_emphasis(seed, caplog, test_all_lines_same_length=True):
    """Pytest function for testing the output of 'log_with_emphasis'.

    The expected output of log_with_emphasis looks similar to this:
    ***************
    ** hello     **
    ** howdy     **
    ** what's up **
    ***************
    """  # noqa: RST212
    # ignoring check because flake8 flags the codeblocks as underlines
    message = generate_random_message(seed)

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


@pytest.mark.parametrize(
    "seed",
    range(NUM_RANDOM_MESSAGES),
    ids=lambda seed: f"seed-{seed}",
)
def test_log_with_emphasis_long_word(seed, caplog):
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
    # fmt: off
    ** this is a very long string that we are not going to match at the top or bottom because it really is too long ok I think this is long enough **
    # fmt: on
    ***********************************************************************************
    """  # noqa: E501,RST212
    # ignoring line length check, and the section underline check because
    # flake8 flags the codeblocks as underlines
    message = generate_random_message(seed, add_long_word=True)

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
