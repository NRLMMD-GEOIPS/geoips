# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Test Pydantic base models for Order-Based Procflow."""

# Python Standard Libraries
import copy
import json
import os

# Third-Party Libraries
import pytest
from pydantic import Field, ValidationError

# GeoIPS Libraries
from geoips.pydantic import bases


@pytest.mark.parametrize(
    "valid_identifier",
    [
        "variable",
        "_underscore_prefixed_variable",
        "variable_aplha_numberic123",
        "_",
        "valid_variable_with_underscore",
    ],
    ids=[
        "simple identifier",
        "underscore-prefixed",
        "alphanumeric",
        "single underscore",
        "contains underscore",
    ],
)
def test_good_valid_python_identifier(valid_identifier):
    """Tests python_identifier call against multiple valid Python identifiers."""
    assert bases.python_identifier(valid_identifier) == valid_identifier


@pytest.mark.parametrize(
    "invalid_identifier, expected_error",
    [
        ("123_starts_with_number", "is not a valid Python identifier"),
        ("invalid_$_symbol", "is not a valid Python identifier"),
        ("variable with_space", "is not a valid Python identifier"),
        ("", "is not a valid Python identifier"),
        ("class", "is a reserved Python keyword"),
    ],
    ids=[
        "starts with number",
        "contains invalid specical character",
        "contains space",
        "empty variable name",
        "uses reserved keyword",
    ],
)
def test_bad_invalid_python_identifier(invalid_identifier, expected_error):
    """Tests python_identifier call against multiple invalid Python identifiers."""
    with pytest.raises(ValueError) as exec_info:
        bases.python_identifier(invalid_identifier)

    assert isinstance(exec_info.value, ValueError), "Exception raised is not ValueError"
    error_message = str(exec_info.value)
    assert (
        expected_error in error_message
    ), f"{error_message} does not match {expected_error}"


# Test mpl_artist_args


class MockArtist:
    """Sample class to test mpl_artist_args call."""

    def __init__(self):
        """For recording all method calls made to the artist object."""
        self.calls = []

    def __call__(self, x, y):
        """Simulate object behavior for test purposes."""
        self.calls.append(("create", x, y))
        return self

    def set(self, **kwargs):
        """Simulate set method behavior in Matplotlib Artists."""
        self.calls.append(("set", kwargs))


@pytest.fixture
def mock_artist():
    """Fixure to provide a fresh instance of MockArtist for each test."""
    return MockArtist()


@pytest.mark.parametrize(
    "sample_args, expected_calls",
    [
        ({"color": "blue", "linewidth": 4, "enabled": True},
         [{"color": "blue"}, {"linewidth": 4}]),
        ({"color": "red", "enabled": False}, [{"color": "red"}]),
        ({}, []),
    ],
)
def test_multi_mpl_artist_args(mock_artist, sample_args, expected_calls):
    """Tests mpl_artist_args call with valid arguments."""
    mock_artist = MockArtist()

    output = bases.mpl_artist_args(sample_args, mock_artist)

    assert mock_artist.calls[0] == ("create", [0, 1], [0, 1])
    set_calls = [call[1] for call in mock_artist.calls if call[0] == "set"]
    assert set_calls == expected_calls
    assert output == sample_args


# lat_lon_coordinate
@pytest.mark.parametrize(
    "valid_coordinates",
    [
        (0, 0),
        (45, 90),
        (-90, -180),
        (90, 180),
        (-90, -180),
        (90, 180),
    ],
    ids=[
        "Null Island",
        "sample valid lat. and long.",
        "South Pole / Minimum Boundary",
        "North Pole / Maximum Boundary",
        "Edge case : Minimum valid boundary",
        "Edge case : Maximum valid boundary",
    ]
)
def test_good_lat_lon_coordinate_valid(valid_coordinates):
    """Tests lat_lon_coordinate call with valid inputs."""
    assert bases.lat_lon_coordinate(valid_coordinates) == valid_coordinates


@pytest.mark.parametrize(
    ("invalid_coordinates", "expected_error"),
    [
        ((-91, 0), "Latitude must be between -90 and 90."),
        ((91, 0), "Latitude must be between -90 and 90."),
        ((0, -181), "Longitude must be between -180 and 180."),
        ((0, 181), "Longitude must be between -180 and 180."),
    ],
    ids=[
        "Latitiude too low",
        "Latitiude too high",
        "Longitude too low",
        "Longitude too high"
    ]
)
def test_bad_lat_lon_coordinate_invalid(invalid_coordinates, expected_error):
    """Tests lat_lon coordinate call with invalid inputs."""
    with pytest.raises(ValueError) as exec_info:
        bases.lat_lon_coordinate(invalid_coordinates)

    assert isinstance(exec_info.value, ValueError), "Exception raised is not ValueError"

    error_message = str(exec_info.value)
    assert (
        expected_error in error_message
    ), f"{error_message} does not match {expected_error}"

# Test PrettyBaseModel


class MockPrettyBaseModel(bases.PrettyBaseModel):
    """Test PrettyBaseModel to test __str__method of PrettyBasemodel."""

    plugin_type: str = Field(description="name of the plugin type")
    plugin_name: str = Field(description="name of the plugin")


def test_good_pretty_base_model_str():
    """Test if the PrettyBaseModel returns JSON data with two-sapce indentation."""
    test_model = MockPrettyBaseModel(plugin_type="Reader", plugin_name="abi_netcdf")

    string_representation_of_model = str(test_model)
    expected_json_format = json.dumps(
        {"plugin_type": "Reader", "plugin_name": "abi_netcdf"}, indent=2
    )

    assert string_representation_of_model == expected_json_format


def test_bad_pretty_base_model_missing_required_field():
    """Test PrettyBaseModel for missing required fields."""
    with pytest.raises(ValidationError) as exec_info:
        MockPrettyBaseModel(plugin_type="Reader")

    error_info = exec_info.value.errors()
    assert len(error_info) == 1
    assert error_info[0]["loc"] == ("plugin_name",)
    assert error_info[0]["type"] == "missing"


def test_bad_pretty_base_model_invalid_field_type():
    """Test PrettyBaseModel for missing required fields."""
    with pytest.raises(ValidationError) as exec_info:
        MockPrettyBaseModel(plugin_type="Reader", plugin_name=123)

    error_info = exec_info.value.errors()
    assert len(error_info) == 1
    assert error_info[0]["loc"] == ("plugin_name",)
    assert error_info[0]["type"] == "string_type"


# Test PluginModel


def test_good_plugin_valid_instance(valid_plugin_data):
    """Test PluginModel with valid inputs."""
    plugin = bases.PluginModel(**valid_plugin_data)

    assert plugin.interface == valid_plugin_data["interface"]
    assert plugin.family == valid_plugin_data["family"]
    assert plugin.name == valid_plugin_data["name"]
    assert plugin.docstring == valid_plugin_data["docstring"]
    assert plugin.package == valid_plugin_data["package"]
    assert plugin.relpath == valid_plugin_data["relpath"]
    assert plugin.abspath == valid_plugin_data["abspath"]


def test_bad_plugin_invalid_instance_additional_field(valid_plugin_data):
    """Test PluginModel with additional field."""
    invalid_data = valid_plugin_data.copy()
    # adding an extra field
    invalid_data["unexpected_field"] = "unexpected_value"

    with pytest.raises(ValidationError) as exec_info:
        bases.PluginModel(**invalid_data)

    error_info = exec_info.value.errors()
    assert any(
        err["type"] == "extra_forbidden" for err in error_info
    ), "expected 'extra_frobidden' error type"
    assert "unexpected_field" in str(
        exec_info.value
    ), "Unexpected field should be mentioned in the error"


# Parameterized test input for a valid docstring test
@pytest.mark.parametrize(
    "docstring",
    ["This is a valid docstring."],
)
def test_good_plugin_model_docstring(valid_plugin_data, docstring):
    """Test PluginModel with a good docstring."""
    data = copy.deepcopy(valid_plugin_data)
    data["docstring"] = docstring
    model = bases.PluginModel(**data)
    assert model.docstring == docstring


# Parameterized test input for multiple invalid docstrings
@pytest.mark.parametrize(
    "invalid_docstring",
    [
        ("This is a \n a multiline docstring.", "The docstring must be one line only."),
        ("Docstring with missing period", "The docstring must end with a period"),
        (
            "docstring starting with lower case and ending with no period",
            "The Docstring should start with a capital letter and end with a period",
        ),
    ],
    ids=[
        "Multiline docstring",
        "Missing period docstring",
        "Start with Capital & end in period",
    ],
)
def test_bad_plugin_model_docstring(valid_plugin_data, invalid_docstring):
    """Test PluginModel with invalid docstring usecases."""
    data = copy.deepcopy(valid_plugin_data)
    data["docstring"] = invalid_docstring

    with pytest.raises(ValueError) as exec_info:
        bases.PluginModel(**data)

    error_info = exec_info.value.errors()
    assert any(error["loc"] == ("docstring",) for error in error_info)
    assert any("valid string" in error["msg"] for error in error_info)


@pytest.mark.parametrize(
    "relpath_valid",
    [
        "relative/path",
        "./relative/path",
        "../parent/path",
    ],
    ids=[
        "simple relative pat",
        "relative path from current directory",
        "relative path from parent directory",
    ],
)
def test_good_plugin_model_relpath(valid_plugin_data, relpath_valid):
    """Test PluginModel with valid relative path instances."""
    data = copy.deepcopy(valid_plugin_data)
    data["relpath"] = relpath_valid
    model = bases.PluginModel(**data)
    assert model.relpath == relpath_valid


@pytest.mark.parametrize(
    "relpath_invalid",
    [
        "/sample/absolute/path",
    ],
    ids=[
        "The 'relpath' must be a relative path",
    ],
)
def test_bad_plugin_model_relpath(valid_plugin_data, relpath_invalid):
    """Test PluginModel with invalid relative path instances."""
    data = copy.deepcopy(valid_plugin_data)
    data["relpath"] = relpath_invalid
    # model = bases.PluginModel(**data)

    with pytest.raises(ValueError) as exec_info:
        bases.PluginModel(**data)

    error_info = exec_info.value.errors()
    assert any(error["loc"] == ("relpath",) for error in error_info)
    assert any("relative path" in error["msg"] for error in error_info)


@pytest.mark.parametrize(
    "abspath_valid",
    [
        "/simple/absolute/path",
        os.path.expanduser("~/user/path"),
    ],
    ids=[
        "simple absolute path",
        "from home dir absolute path",
    ],
)
def test_good_plugin_model_abspath(valid_plugin_data, abspath_valid):
    """Test PluginModel with valid abspath instances."""
    data = copy.deepcopy(valid_plugin_data)
    data["abspath"] = abspath_valid
    model = bases.PluginModel(**data)
    assert model.abspath == abspath_valid


@pytest.mark.parametrize(
    "abspath_invalid",
    [
        "relative/path",
    ],
    ids=[
        "The 'abspath' must be an absolute path",
    ],
)
def test_bad_plugin_model_abspath(valid_plugin_data, abspath_invalid):
    """Test PluginModel with invalid abspath."""
    data = copy.deepcopy(valid_plugin_data)
    data["abspath"] = abspath_invalid

    with pytest.raises(ValidationError) as exec_info:
        bases.PluginModel(**data)

    error_info = exec_info.value.errors()
    assert any(error["loc"] == ("abspath",) for error in error_info)
    assert any("absolute path" in error["msg"] for error in error_info)
