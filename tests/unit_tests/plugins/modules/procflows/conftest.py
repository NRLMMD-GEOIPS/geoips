# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Fixtures for testing Order-Based Procflow-specific utility functions."""

import copy

# Third-Party Libraries
import pytest

# GeoIPS imports
from geoips.constants import PLUGIN_PROVIDED


@pytest.fixture
def workflow_with_plugin_provided():
    """Return workflow containing plugin-provided values."""
    return {
        "spec": {
            "steps": {
                "reader": {
                    "kind": "reader",
                    "arguments": {
                        "test": PLUGIN_PROVIDED,
                        "variables": ["B14BT"],
                    },
                }
            }
        }
    }
