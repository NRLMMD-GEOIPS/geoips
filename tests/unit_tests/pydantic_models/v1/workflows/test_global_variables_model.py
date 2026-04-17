# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Test Order-based procflow GlobalVariablesModel."""

# Third-Party Libraries
import pytest
from pydantic import ValidationError
from datetime import datetime

# GeoIPS Libraries
from geoips.pydantic_models.v1 import workflows

# ---------- happy paths ----------


def test_good_valid_global_variables_model(valid_global_variables_model_data):
    """Instantiates with all fields set; field-by-field equality."""
    fixture_data = valid_global_variables_model_data
    model = workflows.GlobalVariablesModel(**valid_global_variables_model_data)

    assert hasattr(model, "window_start_time")
    assert hasattr(model, "window_end_time")
    assert hasattr(model, "product_name")
    assert hasattr(model, "reader_defined_area_def")
    assert hasattr(model, "no_presectoring")
    assert hasattr(model, "product_db")
    assert hasattr(model, "product_db_writer")
    assert hasattr(model, "product_db_writer_kwargs")

    assert model.window_start_time == fixture_data["window_start_time"]
    assert model.window_end_time == fixture_data["window_end_time"]
    assert model.product_name == fixture_data["product_name"]
    assert model.reader_defined_area_def == fixture_data["reader_defined_area_def"]
    assert model.no_presectoring == fixture_data["no_presectoring"]
    assert model.product_db == fixture_data["product_db"]
    assert model.product_db_writer == fixture_data["product_db_writer"]
    assert model.product_db_writer_kwargs == fixture_data["product_db_writer_kwargs"]


def test_good_global_variables_model_field_defaults():
    """Constructed with no args; assert every default per spec table."""
    model = workflows.GlobalVariablesModel()
    expected_defaults = {
        "window_start_time": None,
        "window_end_time": None,
        "product_name": None,
        "reader_defined_area_def": False,
        "no_presectoring": True,
        "product_db": False,
        "product_db_writer": None,
        "product_db_writer_kwargs": None,
    }

    for field_name, val in expected_defaults.items():
        model_field = getattr(model, field_name)
        assert model_field == val


def test_good_window_start_time_accepts_iso_string():
    """ISO-8601 string for window_start_time coerces to datetime."""
    time_windows = {
        "window_start_time": "2025-01-01T00:00:00",
        "window_end_time": "2025-01-01T01:00:00",
    }
    model = workflows.GlobalVariablesModel(**time_windows)

    assert isinstance(model.window_start_time, datetime)
    assert isinstance(model.window_end_time, datetime)


# ---------- per-field invalid types ----------


def test_bad_global_variables_model_invalid_field_types():
    """Each field rejects a wrong-type value (one big invalid dict)."""
    invalid_test_data = {
        "window_start_time": "not-a-date",
        "window_end_time": "not-a-date",
        "product_name": -999,
        "reader_defined_area_def": "invalid",
        "no_presectoring": "invalid",
        "product_db": "invalid",
        "product_db_writer": -999,
        "product_db_writer_kwargs": "invalid",
    }

    with pytest.raises(ValidationError) as exec_info:
        workflows.GlobalVariablesModel(**invalid_test_data)

    error_info = exec_info.value.errors()

    test_data_errors = {
        "window_start_time": "datetime_from_date_parsing",
        "window_end_time": "datetime_from_date_parsing",
        "product_name": "string_type",
        "reader_defined_area_def": "bool_parsing",
        "no_presectoring": "bool_parsing",
        "product_db": "bool_parsing",
        "product_db_writer": "string_type",
        "product_db_writer_kwargs": "dict_type",
    }
    for field, error_type in test_data_errors.items():
        assert any(
            err["loc"] == (field,) and err["type"] == error_type for err in error_info
        ), f"Expected error for the field '{field}' with the type '{error_type}'."


# ---------- product_db pairing validator (bidirectional) ----------


def test_bad_product_db_true_without_writer():
    """product_db=True with product_db_writer=None raises."""
    product_db_spec = {"product_db": True, "product_db_writer": None}

    with pytest.raises(ValidationError):
        workflows.GlobalVariablesModel(**product_db_spec)


def test_bad_product_db_writer_without_product_db():
    """product_db_writer set with product_db=False raises (reverse direction)."""
    product_db_spec = {"product_db": False, "product_db_writer": "postgres_database"}

    with pytest.raises(ValidationError):
        workflows.GlobalVariablesModel(**product_db_spec)


def test_good_product_db_both_set():
    """product_db=True + writer set -> constructs successfully."""
    product_db_spec = {"product_db": True, "product_db_writer": "postgres_database"}

    model = workflows.GlobalVariablesModel(**product_db_spec)

    assert model.product_db is True


def test_good_product_db_neither_set():
    """Both at defaults -> constructs successfully."""
    product_db_spec = {"product_db": False, "product_db_writer": None}

    model = workflows.GlobalVariablesModel(**product_db_spec)

    assert model.product_db is False


# ---------- window pairing validator (bidirectional) ----------


def test_bad_window_start_without_end():
    """Start time set but end time unset -> raises."""
    time_window_spec = {
        "window_start_time": "2025-01-01T00:00:00",
        "window_end_time": None,
    }

    with pytest.raises(ValidationError):
        workflows.GlobalVariablesModel(**time_window_spec)


def test_bad_window_end_without_start():
    """End time set but start time unset -> raises (reverse direction)."""
    time_window_spec = {
        "window_start_time": None,
        "window_end_time": "2025-01-01T01:00:00",
    }

    with pytest.raises(ValidationError):
        workflows.GlobalVariablesModel(**time_window_spec)


def test_good_window_both_set():
    """Both set -> constructs successfully."""
    time_window_spec = {
        "window_start_time": "2025-01-01T00:00:00",
        "window_end_time": "2025-01-01T01:00:00",
    }

    model = workflows.GlobalVariablesModel(**time_window_spec)

    assert isinstance(model.window_start_time, datetime)


def test_good_window_neither_set():
    """Neither set -> constructs successfully."""
    time_window_spec = {
        "window_start_time": None,
        "window_end_time": None,
    }

    model = workflows.GlobalVariablesModel(**time_window_spec)

    assert model.window_end_time is None
