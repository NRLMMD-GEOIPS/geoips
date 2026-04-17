# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Test Order-based procflow GlobalVariablesModel."""

import copy

# Third-Party Libraries
import pytest
from pydantic import ValidationError

# GeoIPS Libraries
from geoips.pydantic_models.v1 import workflows
from tests.unit_tests.pydantic_models.v1.conftest import valid_global_variables_model_data as base_case

# ---------- happy paths ----------

def test_good_valid_global_variables_model(valid_global_variables_model_data):
    """Instantiates with all fields set; field-by-field equality."""
    fixture_data = base_case()
    model = workflows.GlobalVariablesModel(**valid_global_variables_model_data)

    assert hasattr(model, "window_start_time")
    assert hasattr(model, "window_end_time")
    assert hasattr(model, "product_name")
    assert hasattr(model, "reader_defined_area_def")
    assert hasattr(model, "no_presectoring")
    assert hasattr(model, "product_db")
    assert hasattr(model, "product_db_writer")
    assert hasattr(model, "product_db_writer_kwargs")

    assert model.window_start_time == fixture_data.window_start_time
    assert model.window_end_time == fixture_data.window_end_time
    assert model.product_name == fixture_data.product_name
    assert model.reader_defined_area_def == fixture_data.reader_defined_area_def
    assert model.no_presectoring == fixture_data.no_presectoring
    assert model.product_db == fixture_data.product_db
    assert model.product_db_writer == fixture_data.product_db_writer
    assert model.product_db_writer_kwargs == fixture_data.product_db_writer_kwargs

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

    for field_name, val in expected_defaults:
        model_field = getattr(model, field_name)
        assert model_field == val

def test_good_window_start_time_accepts_iso_string():
    """ISO-8601 string for window_start_time coerces to datetime."""
    # also pair with end_time to satisfy the window validator
    # ...

# ---------- per-field invalid types ----------

def test_bad_global_variables_model_invalid_field_types():
    """Each field rejects a wrong-type value (one big invalid dict)."""
    # mirror test_bad_reader_arguments_model_invalid_field_type structure
    # invalid_test_data = { "window_start_time": "not-a-date", "product_name": 123,
    #                       "reader_defined_area_def": "invalid", ... }
    # assert any(err["loc"] == (field,) and err["type"] == expected_type ...)
    # ...

# ---------- product_db pairing validator (bidirectional) ----------

def test_bad_product_db_true_without_writer():
    """product_db=True with product_db_writer=None raises."""
    # assert "product_db_writer" in error message
    # ...

def test_bad_product_db_writer_without_product_db():
    """product_db_writer set with product_db=False raises (reverse direction)."""
    # ...

def test_good_product_db_both_set():
    """product_db=True + writer set -> constructs successfully."""
    # ...

def test_good_product_db_neither_set():
    """Both at defaults -> constructs successfully."""
    # ...

# ---------- window pairing validator (bidirectional) ----------

def test_bad_window_start_without_end():
    # ...
def test_bad_window_end_without_start():
    # ...
def test_good_window_both_set():
    # ...
def test_good_window_neither_set():
    # ...
