# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit tests for GeoIPS deprecation helpers."""

from pydantic import ValidationError
import pytest

import geoips.deprecation as deprecation


def test_deprecation_message_parsing_full():
    """Test GeoipsDeprecationMessage with full list of fields, all compliant."""
    message = """
        Name: No more stale old approach
        Component: Workflows
        Reference Issue: https://github.com/NRLMMD-GEOIPS/geoips/pull/1539
        Deprecated In: 2.0.0
        Removal In: 3.0.0
        Replacement: Use brand new approach instead
    """
    parsed = deprecation.GeoipsDeprecationMessage.parse_message(message)
    assert parsed.name == "No more stale old approach"
    assert parsed.component == "Workflows"
    assert (
        str(parsed.reference_issue)
        == "https://github.com/NRLMMD-GEOIPS/geoips/pull/1539"
    )
    assert parsed.deprecated_in == "2.0.0"
    assert parsed.remove_in == "3.0.0"
    assert parsed.replacement == "Use brand new approach instead"


def test_deprecation_message_parsing_minimal():
    """Test GeoipsDeprecationMessage with required fields, and nothing more."""
    message = """
        Component: A
        Reference Issue: MISSING
        Deprecated In: 0.0.0
    """
    parsed = deprecation.GeoipsDeprecationMessage.parse_message(message)
    assert parsed.name is None
    assert parsed.component == "A"
    assert parsed.reference_issue == "MISSING"
    assert parsed.deprecated_in == "0.0.0"
    assert parsed.remove_in.startswith("Conditional")
    assert parsed.replacement is None


def test_deprecation_message_parsing_too_long():
    """Test GeoipsDeprecationMessage line length exceedance."""
    template_message = """
        Name: AAA
        Component: BBB
        Reference Issue: https://github.com/NRLMMD-GEOIPS/geoips/#CCC
        Deprecated In: 0.0.0
        Replacement: DDD
    """
    long_name = template_message.replace("AAA", "A" * 71)
    long_component = template_message.replace("BBB", "B" * 41)
    long_url = template_message.replace("CCC", "C" * 80)
    long_replacement = template_message.replace("DDD", "D" * 91)
    with pytest.raises(ValidationError):
        deprecation.GeoipsDeprecationMessage.parse_message(long_name)
    with pytest.raises(ValidationError):
        deprecation.GeoipsDeprecationMessage.parse_message(long_component)
    # We do not currently validate the URL beyond being a URL, so allow to pass
    deprecation.GeoipsDeprecationMessage.parse_message(long_url)
    with pytest.raises(ValidationError):
        deprecation.GeoipsDeprecationMessage.parse_message(long_replacement)


def test_deprecation_message_parsing_missing():
    """Test GeoipsDeprecationMessage when missing required fields."""
    template_message_lines = (
        "Component: A",
        "Reference Issue: MISSING",
        "Deprecated In: 0.0.0",
    )
    missing_component = "\n".join(template_message_lines[1:])
    missing_reference_issue = "\n".join(template_message_lines[::2])
    missing_deprecated_in = "\n".join(template_message_lines[:2])
    with pytest.raises(ValidationError):
        deprecation.GeoipsDeprecationMessage.parse_message(missing_component)
    with pytest.raises(ValidationError):
        deprecation.GeoipsDeprecationMessage.parse_message(missing_reference_issue)
    with pytest.raises(ValidationError):
        deprecation.GeoipsDeprecationMessage.parse_message(missing_deprecated_in)


def test_deprecation_message_parsing_invalid_version():
    """Test GeoipsDeprecationMessage with invalid version."""
    message = """
        Component: A
        Reference Issue: MISSING
        Deprecated In: alpha
    """
    with pytest.raises(ValidationError):
        deprecation.GeoipsDeprecationMessage.parse_message(message)


def test_deprecation_message_parsing_invalid_url():
    """Test GeoipsDeprecationMessage with invalid url."""
    message = """
        Component: A
        Reference Issue: /this/is/not/a/url
        Deprecated In: 0.0.0
    """
    with pytest.raises(ValidationError):
        deprecation.GeoipsDeprecationMessage.parse_message(message)


def test_message_parsing_for_pydeprecate():
    """Ensure that our deprecation message produces expected kwargs for pydeprecate."""
    message = """
        Name: "`chans` argument in Readers"
        Component: Readers
        Reference Issue: https://github.com/NRLMMD-GEOIPS/geoips/issues/953
        Deprecated In: 1.19.0
        Removal In: 2.0.0
        Replacement: "Use `variables` instead"
    """
    kwargs = deprecation._parse_for_pydeprecate(message)
    assert kwargs["message_template"] == (
        "`chans` argument in Readers (Component: Readers) is deprecated as of "
        "v%(deprecated_in)s, and will be removed in v%(remove_in)s. "
        "Replacement/Migration Instructions: Use `variables` instead. See "
        "https://github.com/NRLMMD-GEOIPS/geoips/issues/953 for more information."
    )
    assert kwargs["deprecated_in"] == "1.19.0"
    assert kwargs["remove_in"] == "2.0.0"
