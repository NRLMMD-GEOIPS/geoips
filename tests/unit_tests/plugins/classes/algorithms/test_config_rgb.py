from pydantic import ValidationError
import pytest
import json
import copy

from geoips.plugins.classes.algorithms.config_rgb import ConfigRgbAlgorithmPlugin

class TestConfigRGBFunctionality:
    test_config = {
        "red": {
            "equation": {
                "type": "difference",
                "variables": ["B08BT", "B10BT"]
            },
            "data_range": [-26.2, 0.6],
            "gamma": 1.0,
            "input_units": "kelvin",
            "output_units": "kelvin"
        },
        "green": {
            "equation": {
                "type": "difference",
                "variables": ["B08BT", "B10BT"]
            },
            "data_range": [-26.2, 0.6],
            "gamma": 1.0,
            "input_units": "kelvin",
            "output_units": "kelvin"
        },
        "blue": {
            "equation": {
                "type": "difference",
                "variables": ["B08BT", "B10BT"]
            },
            "data_range": [-26.2, 0.6],
            "gamma": 1.0,
            "input_units": "kelvin",
            "output_units": "kelvin"
        }
    }
    alg = ConfigRgbAlgorithmPlugin()

    def test_get_config_spec(self) -> None:
        self.alg._get_config_spec(self.test_config)

    def test_get_invalid_config_spec(self) -> None:
        test_copy_config = copy.deepcopy(self.test_config)

        test_copy_config["red"] = {}

        with pytest.raises(ValueError):
            self.alg._get_config_spec(test_copy_config)
