"""Unit Test for Log With Emphasis Function using Pytest and CapLog."""

import pytest
from geoips.commandline.log_setup import log_with_emphasis
import logging
import random
import string

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
    max_message_len = min(80, len(message))
    assert max_message_len <= 80, "Max emphasis in '*' is longer than 80 chars."
    log_with_emphasis(LOG.info, [message])
    assert "    " + "*" * max_message_len in caplog.text
    assert "    " + message in caplog.text
    assert "    " + "*" * max_message_len in caplog.text
    assert "\n" in caplog.text
