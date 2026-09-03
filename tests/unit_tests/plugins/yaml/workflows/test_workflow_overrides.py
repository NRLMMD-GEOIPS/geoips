"""Unit test module for testing workflow overrides."""

# cspell: ignore soverrides

from collections import OrderedDict
from copy import deepcopy
import tempfile

import pytest

from geoips.interfaces.yaml_based.workflows import workflows

tmpdir = tempfile.gettempdir()


@pytest.fixture
def sample_workflow():
    """Return a representative workflow dictionary."""
    return {
        "name": "dummy_workflow",
        "interface": "workflows",
        "family": "standard",
        "apiVersion": "geoips/v1",
        "docstring": "Dummy workflow.",
        "spec": {
            "steps": {
                "reader": {
                    "kind": "reader",
                    "arguments": {
                        "self_register": "HIGH",
                        "satellite_zenith_angle_cutoff": 70,
                    },
                },
                "algorithm": {
                    "kind": "algorithm",
                    "arguments": {
                        "output_units": "celsius",
                    },
                },
                "nested_workflow": {
                    "kind": "workflow",
                    "spec": {
                        "steps": {
                            "nested_algorithm": {
                                "kind": "algorithm",
                                "arguments": {
                                    "output_units": "celsius",
                                },
                            }
                        }
                    },
                },
            }
        },
        "arguments": {
            "global": {
                "logging_level": "INFO",
                "satellite_zenith_angle_cutoff": 90,
            },
            "reader.self_register": "LOW",
        },
    }


##########################################
#
# OVERRIDE TYPE PARSING TESTS
#
##########################################


def test_global_override_type_string_value():
    """Test parsing a global override containing a string value."""
    result = workflows.global_override_type("logging_level=INFO")

    assert result == {
        "argument": "logging_level",
        "value": "INFO",
    }


def test_global_override_type_yaml_casting():
    """Test automatic YAML type conversion for global overrides.

    Ensures yaml.safe_load is applied to the value portion of the
    override string so numeric values are converted to their
    corresponding Python types.
    """
    result = workflows.global_override_type("satellite_zenith_angle_cutoff=85")

    assert result == {
        "argument": "satellite_zenith_angle_cutoff",
        "value": 85,
    }


def test_step_override_type():
    """Test parsing a step override containing nested keys.

    Verifies that the step identifier, intermediate keys, argument,
    and value are extracted correctly from a nested override path.
    """
    result = workflows.step_override_type("reader.self_register=LOW")

    assert result == {
        "step_id": "reader",
        "keys": [],
        "argument": "self_register",
        "value": "LOW",
    }


def test_step_override_type_no_nested_keys():
    """Test parsing a step override that targets a top-level argument.

    Verifies that an empty keys list is returned when no intermediate
    path components exist between the step id and argument name.
    """
    result = workflows.step_override_type("reader.self_register=LOW")

    assert result == {
        "step_id": "reader",
        "keys": [],
        "argument": "self_register",
        "value": "LOW",
    }


def test_step_override_type_invalid_key():
    """Test failure when a step override contains no argument path.

    A valid step override must contain at least a step identifier
    and argument name separated by a period.
    """
    with pytest.raises(ValueError, match="Must have at least"):
        workflows.step_override_type("reader=LOW")


##########################################
#
# STRING-BASED OVERRIDE TESTS
#
##########################################


def test_set_nested():
    """Test setting nested dictionary values."""
    steps = {
        "reader": {
            "arguments": {
                "self_register": "HIGH",
            }
        }
    }

    result = workflows._set_nested(
        steps,
        "reader",
        [],
        "self_register",
        "LOW",
    )

    assert result["reader"]["arguments"]["self_register"] == "LOW"


def test_override_step(sample_workflow):
    """Test overriding a specific step.

    Parameters
    ----------
    sample_workflow: pytest.fixture[dict]
        A dummy workflow to perform unit tests on.
    """
    override = {
        "step_id": "reader",
        "keys": [],
        "argument": "self_register",
        "value": "LOW",
    }

    steps = deepcopy(sample_workflow["spec"]["steps"])

    result = workflows._override_step(steps, override)

    assert result["reader"]["arguments"]["self_register"] == "LOW"


def test_override_global(sample_workflow):
    """Test overriding all matching global arguments.

    Parameters
    ----------
    sample_workflow: pytest.fixture[dict]
        A dummy workflow to perform unit tests on.
    """
    override = {
        "argument": "satellite_zenith_angle_cutoff",
        "value": 80,
    }

    steps = deepcopy(sample_workflow["spec"]["steps"])

    result = workflows._override_global(steps, override)

    assert result["reader"]["arguments"]["satellite_zenith_angle_cutoff"] == 80


def test_override_workflow_string_format_from_dict(sample_workflow):
    """Test applying all string-based overrides from a dictionary representation.

    Parameters
    ----------
    sample_workflow: pytest.fixture[dict]
        A dummy workflow to perform unit tests on.
    """
    workflow = deepcopy(sample_workflow)

    goverrides = [
        {
            "argument": "satellite_zenith_angle_cutoff",
            "value": 85,
        }
    ]

    soverrides = [
        {
            "step_id": "reader",
            "keys": [],
            "argument": "self_register",
            "value": "LOW",
        },
        {
            "step_id": "algorithm",
            "keys": [],
            "argument": "output_units",
            "value": "kelvin",
        },
    ]

    result = workflows._override_workflow_string_format(
        workflow,
        goverrides=goverrides,
        soverrides=soverrides,
        grab_bases=False,
    )

    steps = result["spec"]["steps"]

    assert steps["reader"]["arguments"]["self_register"] == "LOW"
    assert steps["reader"]["arguments"]["satellite_zenith_angle_cutoff"] == 85
    assert steps["algorithm"]["arguments"]["output_units"] == "kelvin"


def test_override_workflow_string_format_from_string(sample_workflow):
    """Test applying all string-based overrides from string-based representation.

    Parameters
    ----------
    sample_workflow: pytest.fixture[dict]
        A dummy workflow to perform unit tests on.
    """
    workflow = deepcopy(sample_workflow)

    goverrides = ["satellite_zenith_angle_cutoff=85"]

    soverrides = ["reader.self_register=LOW"]

    result = workflows._override_workflow_string_format(
        workflow,
        goverrides=goverrides,
        soverrides=soverrides,
        grab_bases=False,
    )

    steps = result["spec"]["steps"]

    assert steps["reader"]["arguments"]["self_register"] == "LOW"
    assert steps["reader"]["arguments"]["satellite_zenith_angle_cutoff"] == 85


##########################################
#
# DICT-BASED OVERRIDE TESTS
#
##########################################


def test_override_workflow_dict_format(sample_workflow):
    """Test dict-based workflow overrides.

    Parameters
    ----------
    sample_workflow: pytest.fixture[dict]
        A dummy workflow to perform unit tests on.
    """
    workflow = deepcopy(sample_workflow)

    goverrides = {
        "satellite_zenith_angle_cutoff": 90,
    }

    soverrides = {
        "reader": {
            "self_register": "LOW",
        }
    }

    result = workflows._override_workflow_dict_format(
        workflow,
        goverrides=goverrides,
        soverrides=soverrides,
    )

    steps = result["spec"]["steps"]

    assert steps["reader"]["arguments"]["satellite_zenith_angle_cutoff"] == 90

    assert steps["reader"]["arguments"]["self_register"] == "LOW"


##########################################
#
# OUTPUT CHECKER OVERRIDE TESTS
#
##########################################


def test_insert_after_key():
    """Test inserting a new step after a target step."""
    steps = OrderedDict(
        {
            "reader": {
                "kind": "reader",
                "arguments": {},
            },
            "algorithm": {
                "kind": "algorithm",
                "arguments": {},
            },
        }
    )

    new_value = {
        "kind": "output_checker",
        "arguments": {"compare_path": f"{tmpdir}/output.png"},
        "output_checker_name": "image",
    }

    result = workflows._insert_after_key(
        steps,
        target_key="reader",
        new_key="output_checker1",
        new_value=deepcopy(new_value),
    )

    keys = list(result.keys())

    assert keys == [
        "reader",
        "output_checker1",
        "algorithm",
    ]

    assert result["output_checker1"] == new_value


def test_insert_after_key_missing_target():
    """Test failure when attempting to insert after a missing key.

    Verifies that a KeyError is raised when the requested insertion
    point does not exist within the workflow steps mapping.
    """
    with pytest.raises(KeyError, match="Could not find key"):
        workflows._insert_after_key(
            {"reader": {}},
            target_key="algorithm",
            new_key="output_checker1",
            new_value={
                "full_test_policy": "always",
                "compare_path": f"{tmpdir}/test.png",
            },
        )


def test_build_output_checker_step_requires_output_formatter_target():
    """Test output checker overrides require an output formatter target."""
    with pytest.raises(ValueError, match="must target an output_formatter"):
        workflows._build_output_checker_step(
            "algorithm",
            {
                "kind": "algorithm",
                "arguments": {},
            },
            {
                "full_test_policy": "always",
                "compare_path": f"{tmpdir}/test.png",
            },
        )


def test_build_output_checker_step():
    """Test building an output checker step from a workflow test override."""
    result = workflows._build_output_checker_step(
        "output_formatter",
        {
            "kind": "output_formatter",
            "arguments": {},
        },
        {
            "full_test_policy": "always",
            "compare_path": f"{tmpdir}/output.png",
            "threshold": 5,
            "output_checker_name": "image",
        },
    )

    assert result == {
        "full_test_policy": "always",
        "name": "image",
        "arguments": {
            "compare_path": f"{tmpdir}/output.png",
            "threshold": 5,
        },
        "depends_on": ["output_formatter"],
        "kind": "output_checker",
    }


def test_apply_output_checker_override():
    """Test applying an output checker override to workflow steps.

    Ensures that a new output checker step is inserted after the
    specified workflow step when a leaf override containing a
    full_test_policy field is encountered.
    """
    steps = OrderedDict(
        {
            "reader": {
                "kind": "reader",
                "arguments": {},
            },
            "output_formatter": {
                "kind": "output_formatter",
                "arguments": {},
            },
        }
    )

    override = {
        "output_formatter": {
            "full_test_policy": "always",
            "compare_path": f"{tmpdir}/output.png",
            "output_checker_name": "image",
        }
    }

    result = workflows._apply_output_checker_override(
        deepcopy(steps),
        override,
    )

    assert "output_checker1" in result
    assert result["output_checker1"]["name"] == "image"

    keys = list(result.keys())
    assert keys.index("output_checker1") == (keys.index("output_formatter") + 1)
    assert result["output_checker1"]["depends_on"] == ["output_formatter"]


def test_apply_output_checker_override_missing_nested_key():
    """Test failure when a nested override references a missing key.

    Verifies that a KeyError is raised when recursion attempts to
    traverse a workflow hierarchy that does not exist.
    """
    steps = {
        "reader": {
            "arguments": {},
        }
    }

    override = {
        "missing_step": {
            "full_test_policy": "always",
            "compare_path": f"{tmpdir}/output.png",
        }
    }

    with pytest.raises(KeyError, match="Could not find key"):
        workflows._apply_output_checker_override(
            steps,
            override,
        )


##########################################
#
# CONVERT OVERRIDES TO STRING FORMAT TESTS
#
##########################################


def test_convert_override_dict_to_string_format(sample_workflow):
    """Test conversion of workflow test section overrides to CLI format (string-based).

    Ensures that global, kind, and step overrides are converted into
    the string representation accepted by the CLI.
    """
    goverrides, soverrides = workflows._convert_override_dict_to_string_format(
        sample_workflow
    )

    assert goverrides == [
        "logging_level=INFO",
        "satellite_zenith_angle_cutoff=90",
    ]

    assert soverrides == [
        "reader.self_register=LOW",
    ]


def test_convert_override_dict_to_string_format_nested():
    """Test conversion of nested override dictionaries.

    Verifies that deeply nested override structures are flattened
    into the expected dot-delimited string representation.
    """
    workflow = {
        "arguments": {
            "abi:Infrared.algorithm.output_units": "kelvin",
        },
    }

    goverrides, soverrides = workflows._convert_override_dict_to_string_format(workflow)

    assert soverrides == ["abi:Infrared.algorithm.output_units=kelvin"]
