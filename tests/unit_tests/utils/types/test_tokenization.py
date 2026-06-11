# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Tests for dask-based step output tokenization."""

from unittest.mock import patch

import numpy as np
import xarray as xr

from geoips.utils.types.tokenization import (
    compute_token,
    compute_arguments_hash,
    compute_step_output_token,
)


class TestComputeToken:
    """Stability tests for the low-level token helper."""

    def test_same_objects_produce_same_token(self):
        """Identical inputs produce identical tokens."""
        t1 = compute_token("hello", 42)
        t2 = compute_token("hello", 42)
        assert t1 == t2
        assert t1.startswith("dask:")

    def test_different_objects_produce_different_token(self):
        """Distinct inputs produce distinct tokens."""
        t1 = compute_token("hello", 42)
        t2 = compute_token("hello", 43)
        assert t1 != t2


class TestComputeArgumentsHash:
    """Tests for argument-dict tokenization."""

    def test_identical_dicts_hash_identically(self):
        """Two dicts with the same content but different insertion orders."""
        args1 = {"a": 1, "b": 2}
        args2 = {"b": 2, "a": 1}
        assert compute_arguments_hash(args1) == compute_arguments_hash(args2)

    def test_different_values_produce_different_hash(self):
        """A different argument value changes the hash."""
        h1 = compute_arguments_hash({"variables": ["B14BT"]})
        h2 = compute_arguments_hash({"variables": ["B08BT"]})
        assert h1 != h2


class TestComputeStepOutputToken:
    """Tests for per-step output_token computation."""

    def test_same_output_produces_same_token(self):
        """Repeated calls with identical state produce identical tokens."""
        ds = xr.Dataset({"var": ("x", [1.0, 2.0, 3.0])})
        t1 = compute_step_output_token(
            ds,
            plugin_name="test",
            plugin_kind="reader",
            arguments={"chans": [1, 2]},
        )
        t2 = compute_step_output_token(
            ds,
            plugin_name="test",
            plugin_kind="reader",
            arguments={"chans": [1, 2]},
        )
        assert t1 == t2
        assert t1.startswith("dask:")

    def test_different_plugin_name_changes_token(self):
        """A different plugin name changes the token."""
        ds = xr.Dataset({"var": ("x", [1.0, 2.0])})
        t1 = compute_step_output_token(
            ds, plugin_name="reader_a", plugin_kind="reader", arguments={}
        )
        t2 = compute_step_output_token(
            ds, plugin_name="reader_b", plugin_kind="reader", arguments={}
        )
        assert t1 != t2

    def test_different_arguments_change_token(self):
        """A different arguments dict changes the token."""
        ds = xr.Dataset({"var": ("x", [1.0, 2.0])})
        t1 = compute_step_output_token(
            ds,
            plugin_name="alg",
            plugin_kind="algorithm",
            arguments={"radius_km": 300},
        )
        t2 = compute_step_output_token(
            ds,
            plugin_name="alg",
            plugin_kind="algorithm",
            arguments={"radius_km": 500},
        )
        assert t1 != t2

    def test_different_upstream_tokens_change_token(self):
        """Different upstream tokens propagate into the output token."""
        ds = xr.Dataset({"var": ("x", [1.0])})
        t1 = compute_step_output_token(
            ds,
            plugin_name="alg",
            plugin_kind="algorithm",
            arguments={},
            upstream_tokens={"reader": "dask:aaa"},
        )
        t2 = compute_step_output_token(
            ds,
            plugin_name="alg",
            plugin_kind="algorithm",
            arguments={},
            upstream_tokens={"reader": "dask:bbb"},
        )
        assert t1 != t2

    def test_numpy_array_tokenization(self):
        """Numpy arrays tokenize consistently."""
        arr = np.array([[1.0, 2.0], [3.0, 4.0]])
        t1 = compute_step_output_token(
            arr, plugin_name="np_plug", plugin_kind="algorithm", arguments={}
        )
        t2 = compute_step_output_token(
            arr, plugin_name="np_plug", plugin_kind="algorithm", arguments={}
        )
        assert t1 == t2

    def test_untokenizable_fallback(self):
        """Untokenizable types produce a sentinel string."""
        with patch(
            "geoips.utils.types.tokenization.compute_token",
            side_effect=TypeError("cannot tokenize"),
        ):
            token = compute_step_output_token(
                object(),
                plugin_name="p",
                plugin_kind="reader",
                arguments={},
            )
            assert token.startswith("untokenizable:")
