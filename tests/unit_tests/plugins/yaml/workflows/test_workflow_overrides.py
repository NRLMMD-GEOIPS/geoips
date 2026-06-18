"""Unit test module for testing workflow overrides."""

# cspell: ignore koverrides, soverrides

from collections import OrderedDict
from copy import deepcopy

import pytest

from geoips.errors import PluginError
from geoips.interfaces.yaml_based.workflows import workflows


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
        "test": {
            "globals": {
                "logging_level": "INFO",
            },
            "kinds": {
                "algorithms": {
                    "output_units": "kelvin",
                }
            },
            "steps": {
                "reader": {
                    "self_register": "LOW",
                }
            },
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


def test_kind_override_type():
    """Test parsing a valid kind override string.

    Ensures the kind name, argument name, and value are extracted
    correctly from a valid override specification.
    """
    result = workflows.kind_override_type("algorithm.output_units=kelvin")

    assert result == {
        "kind": "algorithm",
        "argument": "output_units",
        "value": "kelvin",
    }


def test_kind_override_type_invalid_key_format():
    """Test failure when a kind override key is improperly formatted.

    A valid kind override must contain exactly one period separating
    the kind name and argument name.
    """
    with pytest.raises(ValueError, match="Must be in the format"):
        workflows.kind_override_type("algorithm.output.units=kelvin")


def test_step_override_type():
    """Test parsing a step override containing nested keys.

    Verifies that the step identifier, intermediate keys, argument,
    and value are extracted correctly from a nested override path.
    """
    result = workflows.step_override_type("reader.spec.arguments.self_register=LOW")

    assert result == {
        "step_id": "reader",
        "keys": ["spec", "arguments"],
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


def test_override_kind(sample_workflow):
    """Test overriding all steps of a given kind.

    Parameters
    ----------
    sample_workflow: pytest.fixture[dict]
        A dummy workflow to perform unit tests on.
    """
    override = {
        "kind": "algorithm",
        "argument": "output_units",
        "value": "kelvin",
    }

    steps = deepcopy(sample_workflow["spec"]["steps"])

    result = workflows._override_kind(steps, override)

    assert result["algorithm"]["arguments"]["output_units"] == "kelvin"


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

    koverrides = [
        {
            "kind": "algorithms",
            "argument": "output_units",
            "value": "kelvin",
        }
    ]

    soverrides = [
        {
            "step_id": "reader",
            "keys": [],
            "argument": "self_register",
            "value": "LOW",
        }
    ]

    result = workflows._override_workflow_string_format(
        workflow,
        goverrides=goverrides,
        koverrides=koverrides,
        soverrides=soverrides,
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

    koverrides = ["algorithms.output_units=kelvin"]

    soverrides = ["reader.self_register=LOW"]

    result = workflows._override_workflow_string_format(
        workflow,
        goverrides=goverrides,
        koverrides=koverrides,
        soverrides=soverrides,
    )

    steps = result["spec"]["steps"]

    assert steps["reader"]["arguments"]["self_register"] == "LOW"
    assert steps["reader"]["arguments"]["satellite_zenith_angle_cutoff"] == 85
    assert steps["algorithm"]["arguments"]["output_units"] == "kelvin"


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

    koverrides = {
        "algorithms": {
            "output_units": "kelvin",
        }
    }

    soverrides = {
        "reader": {
            "self_register": "LOW",
        }
    }

    result = workflows._override_workflow_dict_format(
        workflow,
        goverrides=goverrides,
        koverrides=koverrides,
        soverrides=soverrides,
    )

    steps = result["spec"]["steps"]

    assert steps["reader"]["arguments"]["satellite_zenith_angle_cutoff"] == 90

    assert steps["algorithm"]["arguments"]["output_units"] == "kelvin"

    assert steps["reader"]["arguments"]["self_register"] == "LOW"


##########################################
#
# OUTPUT CHECKER OVERRIDE TESTS
#
##########################################


def test_insert_after_key():
    """Test inserting a new output checker step after a target step.

    Ensures the new step is inserted immediately after the target
    step and that required output checker metadata is populated.
    """
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
        "policy": "always",
        "arguments": {
            "compare_path": "/tmp/output.png",
        },
        "name": "image",
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

    assert result["output_checker1"]["kind"] == "output_checker"


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
                "policy": "always",
                "arguments": {
                    "compare_path": "/tmp/test.png",
                },
            },
        )


def test_insert_after_key_invalid_override_format():
    """Test failure when an output checker override lacks arguments.

    Verifies that improperly formatted workflow test overrides raise
    a PluginError when neither 'arguments' nor
    'output_checker_arguments' are present.
    """
    with pytest.raises(PluginError, match="improperly formatted"):
        workflows._insert_after_key(
            {"reader": {}},
            target_key="reader",
            new_key="output_checker1",
            new_value={
                "policy": "always",
            },
        )


def test_apply_output_checker_override():
    """Test applying an output checker override to workflow steps.

    Ensures that a new output checker step is inserted after the
    specified workflow step when a leaf override containing a
    policy field is encountered.
    """
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

    override = {
        "reader": {
            "policy": "always",
            "arguments": {
                "compare_path": "/tmp/output.png",
            },
            "name": "image",
        }
    }

    result = workflows._apply_output_checker_override(
        deepcopy(steps),
        override,
    )

    assert "output_checker1" in result

    keys = list(result.keys())
    assert keys.index("output_checker1") == (keys.index("reader") + 1)


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
            "policy": "always",
            "arguments": {
                "compare_path": "/tmp/output.png",
            },
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
    goverrides, koverrides, soverrides = (
        workflows._convert_override_dict_to_string_format(sample_workflow)
    )

    assert goverrides == [
        "logging_level=INFO",
    ]

    assert koverrides == [
        "algorithms.output_units=kelvin",
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
        "test": {
            "steps": {
                "abi:Infrared": {
                    "spec": {
                        "steps": {
                            "algorithm": {
                                "output_units": "kelvin",
                            },
                        }
                    }
                }
            }
        }
    }

    _, _, soverrides = workflows._convert_override_dict_to_string_format(workflow)

    assert soverrides == ["abi:Infrared.spec.steps.algorithm.output_units=kelvin"]


def test_convert_override_dict_to_string_format_empty_mapping():
    """Test that empty override mappings are ignored.

    Verifies that empty dictionaries within the workflow test section
    do not generate override strings.
    """
    workflow = {
        "test": {
            "globals": {
                "logging_level": {},
            }
        }
    }

    goverrides, koverrides, soverrides = (
        workflows._convert_override_dict_to_string_format(workflow)
    )

    assert goverrides == []
    assert koverrides == []
    assert soverrides == []
