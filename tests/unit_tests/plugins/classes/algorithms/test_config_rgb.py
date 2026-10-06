"""Test the `config_rgb` algorithm plugin class."""

import ast
import copy

import numpy as np
import pandas as pd
import pytest
import scipy
from geoips.plugins.classes.algorithms.config_rgb import ConfigRgbAlgorithmPlugin


class TestConfigRGBFunctionality:
    """Test the base functionality of the algorithm."""

    def setup_method(self) -> None:
        self.test_config = {
            "red": {
                "equation": {"expression": "B10BT - B08BT", "variables": ["B08BT", "B10BT"]},
                "data_range": [-26.2, 0.6],
                "gamma": 1.0,
                "input_units": "kelvin",
                "output_units": "kelvin",
            },
            "green": {
                "equation": {"expression": "B10BT - B08BT", "variables": ["B08BT", "B10BT"]},
                "data_range": [-26.2, 0.6],
                "gamma": 1.0,
                "input_units": "kelvin",
                "output_units": "kelvin",
            },
            "blue": {
                "equation": {"expression": "B10BT - B08BT", "variables": ["B08BT", "B10BT"]},
                "data_range": [-26.2, 0.6],
                "gamma": 1.0,
                "input_units": "kelvin",
                "output_units": "kelvin",
            },
        }
        self.alg = ConfigRgbAlgorithmPlugin()

    def test_get_config_spec(self) -> None:
        """Test getting the spec based on the config."""
        self.alg._get_config_spec(self.test_config)

    def test_get_invalid_config_spec(self) -> None:
        """Test getting the spec with an invalid config."""
        test_copy_config = copy.deepcopy(self.test_config)

        test_copy_config["red"] = {}

        with pytest.raises(ValueError):
            self.alg._get_config_spec(test_copy_config)

class TestExpressionEvaluator:
    """Test expression evaluation."""

    def setup_method(self) -> None:
        self.alg = ConfigRgbAlgorithmPlugin()
        self.variables = {"x": np.array([1, 2, 3]), "y": np.array([4, 5, 6])}

    def test_resolve_function_valid(self):
        node = ast.parse("np.sin", mode="eval").body

        res = self.alg._resolve_function(node)

        assert res is np.sin

    def test_resolve_function_invalid_module(self):
        node = ast.parse("bogus.bogus", mode="eval").body

        with pytest.raises(ValueError, match="Module 'bogus' is not allowed"):
            self.alg._resolve_function(node)

    def test_resolve_function_invalid_method(self):
        node = ast.parse("np.bogus", mode="eval").body

        with pytest.raises(ValueError, match="Error getting function from expression"):
            self.alg._resolve_function(node)

    def test_safe_eval_valid(self):
        res = self.alg.safe_eval("x + y", self.variables)

        assert type(res) == np.ndarray
        assert np.array_equal(res, np.array([5, 7, 9]))

    def test_safe_eval_valid_with_numpy_function(self):
        res = self.alg.safe_eval("np.sin(x)", self.variables)

        assert type(res) == np.ndarray
        assert np.array_equal(res, np.sin(self.variables["x"]))

    def test_safe_eval_valid_with_numpy_function_2(self):
        res = self.alg.safe_eval("np.sin(x) - np.cos(y)", self.variables)

        expected = np.sin(self.variables["x"]) - np.cos(self.variables["y"])
        assert type(res) == np.ndarray
        assert np.array_equal(res, expected)

    def test_safe_eval_valid_with_scipy_function(self):
        res = self.alg.safe_eval("scipy.signal.detrend(x)", self.variables)

        expected = scipy.signal.detrend(self.variables["x"])
        assert type(res) == np.ndarray
        assert np.array_equal(res, expected)

    def test_safe_eval_valid_with_pandas_function(self):
        res = self.alg.safe_eval("pd.isna(x)", self.variables)

        expected = pd.isna(self.variables["x"])
        assert type(res) == np.ndarray
        assert np.array_equal(res, expected)

    def test_safe_eval_get_non_ndarray(self):
        with pytest.raises(
            ValueError,
            match="Provided expression returned <class 'pandas.DataFrame'>"
            " instead of np.ndarray",
        ):
            self.alg.safe_eval("pd.DataFrame(x)", self.variables)
    def test_raw_value(self):
        res = self.alg.safe_eval("x", self.variables)

        assert np.array_equal(res, self.variables["x"])
