# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit tests for GeoIPS deprecation helpers."""

from typing_extensions import deprecated

from pydantic import ValidationError
import pytest

import geoips.deprecation as deprecation


def test_deprecation_message_parsing_full():
    """Test GeoipsDeprecationMessage with full list of fields, all compliant."""
    message = """
        Behavior: The stale old approach
        Component: Workflows
        Reference Issue: https://github.com/NRLMMD-GEOIPS/geoips/pull/1539
        Deprecated In: 2.0.0
        Removal In: 3.0.0
        Replacement: Use brand new approach instead
    """
    parsed = deprecation.GeoipsDeprecationMessage.parse_message(message)
    assert parsed.name == "The stale old approach"
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
        Entity/Behavior: AAA
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
        Entity/Behavior: "`chans` argument in Readers"
        Component: Readers
        Reference Issue: https://github.com/NRLMMD-GEOIPS/geoips/issues/953
        Deprecated In: 1.19.0
        Removal In: 2.0.0
        Replacement: "Use `variables` instead"
    """
    # As expected
    kwargs = deprecation._parse_for_pydeprecate(message)
    correct_output_message = (
        "`chans` argument in Readers (Component: Readers) is deprecated as of "
        "v%(deprecated_in)s, and will be removed in v%(remove_in)s. "
        "Replacement/Migration Instructions: Use `variables` instead. See "
        "https://github.com/NRLMMD-GEOIPS/geoips/issues/953 for more information."
    )
    assert kwargs["message_template"] == correct_output_message
    assert kwargs["deprecated_in"] == "1.19.0"
    assert kwargs["remove_in"] == "2.0.0"
    # Test message_template warning
    with pytest.warns(UserWarning, match="overwrite"):
        kwargs = deprecation._parse_for_pydeprecate(
            message, message_template="In: v%(deprecated_in)s, Out: v%(remove_in)s"
        )
    assert kwargs["message_template"] == correct_output_message
    # Test omission of docstring args
    kwargs = deprecation._parse_for_pydeprecate(message, include_docstring_args=False)
    assert "update_docstring" not in kwargs


def test_message_parsing_not_for_pydeprecate():
    """Ensure that our deprecation message parsing excluding pydeprecate options."""
    message = deprecation.GeoipsDeprecationMessage.parse_message("""
        Component: CLI
        Deprecated In: 2.0.0
        Removal In: 3.0.0
        Reference Issue: MISSING
    """).to_string()
    assert message == (
        "This (as a part of CLI) is deprecated as of v2.0.0, and will be removed in "
        "v3.0.0."
    )


def test_pending_deprecation_with_non_geoips_format():
    """Ensure that our pending deprecation warning works, with non-GeoIPS format."""
    with pytest.warns(
        deprecation.GeoipsPendingDeprecationWarning, match="removed. Use"
    ):
        deprecation.pending_deprecation_warning(
            "This will be removed.\nUse this instead."
        )


def test_deprecate_callable():
    """Test GeoIPS wrapper of PyDeprecate for callables."""

    @deprecation.deprecate_callable()
    @deprecated("""
        Component: Scripting
        Reference Issue: MISSING
        Deprecated In: 2.0.0
    """)
    def test_function():
        pass

    with pytest.warns(
        deprecation.GeoipsDeprecationWarning, match="deprecated as of v2.0.0."
    ):
        test_function()


def test_deprecate_argument():
    """Test GeoIPS wrapper of PyDeprecate for callable arguments."""

    @deprecation.deprecate_argument(
        """
            Component: Scripting
            Reference Issue: MISSING
            Deprecated In: 2.0.0
        """,
        args_mapping={"old": "new"},
    )
    def test_function(new: str):
        return f"{new}, {new}!"

    with pytest.warns(
        deprecation.GeoipsDeprecationWarning, match="deprecated as of v2.0.0."
    ):
        assert test_function(old="a") == "a, a!"


def test_deprecate_class():
    """Test GeoIPS wrapper of PyDeprecate for classes."""

    @deprecation.deprecate_class()
    @deprecated("""
        Component: Scripting
        Reference Issue: MISSING
        Deprecated In: 2.0.0
    """)
    class OldClass:
        old: bool = True

        def __init__(self, old=True):
            self.old = old

    with pytest.warns(
        deprecation.GeoipsDeprecationWarning, match="deprecated as of v2.0.0."
    ):
        OldClass()


def test_deprecate_instance():
    """Test GeoIPS wrapper of PyDeprecate for instances."""
    old_thing = {"message": "Hello, world!"}
    old_thing = deprecation.deprecate_instance(
        old_thing,
        """
            Component: Scripting
            Reference Issue: MISSING
            Deprecated In: 2.0.0
        """,
    )
    with pytest.warns(
        deprecation.GeoipsDeprecationWarning, match="deprecated as of v2.0.0."
    ):
        old_thing["message"]
