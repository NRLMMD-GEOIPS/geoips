# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Drift guards keeping the config schema, env-var map, and legacy dict in sync.

``geoips.config.schema.GEOIPS_ENV_MAP`` is the authoritative, canonical list
of every environment variable GeoIPS supports and the setting each maps to.
These tests ensure that:

* every mapping in ``GEOIPS_ENV_MAP`` points at a real setting,
* every setting is reachable from an environment variable (so new settings
  cannot be added silently), and
* the backward-compatible flat "legacy dict" stays consistent with the map.

Together these guarantee the reviewer's requirement that the env var mappings
"continue working" and that there is "a clear way to track" available
settings.
"""

from functools import reduce

import pydantic
import pytest

from geoips.config.config import GeoIPSConfig
from geoips.config.schema import GEOIPS_ENV_MAP, GeoSettings

# Settings that are auto-derived at load time and intentionally have no env var.
AUTO_DERIVED_FIELDS = {"base_path", "home"}

# Legacy flat-dict keys that are auto-derived and thus have no GEOIPS_ENV_MAP
# entry (they cannot be overridden via a single environment variable).
AUTO_DERIVED_LEGACY_KEYS = {"BASE_PATH", "HOME"}

# Environment variables that are aliases for another variable's setting. They
# share a setting path with a canonical variable, so they do not each get a
# distinct legacy-dict key.
ENV_VAR_ALIASES = {"GEOIPS_NO_COLOR"}  # alias of NO_COLOR (features.no_color)


def _nested_model(annotation):
    """Return the nested pydantic model for an annotation, or None."""
    return annotation if getattr(annotation, "model_fields", None) else None


def _field_leaf_paths(name, field, prefix):
    """Return the set of dotted leaf paths contributed by a single field."""
    nested = _nested_model(field.annotation)
    if nested is None:
        return frozenset({f"{prefix}{name}"})
    return _leaf_field_paths(nested, f"{prefix}{name}.")


def _leaf_field_paths(model_cls, prefix=""):
    """Return the set of dotted leaf field paths for a pydantic model tree."""
    return frozenset().union(
        *(
            _field_leaf_paths(name, field, prefix)
            for name, field in model_cls.model_fields.items()
        )
    )


def _resolve_field(model_cls, part):
    """Return the annotation for ``part`` on ``model_cls``, or None if absent."""
    fields = getattr(model_cls, "model_fields", None) or {}
    field = fields.get(part)
    return field.annotation if field is not None else None


def _field_path_is_valid(model_cls, dotted_path):
    """Return True if ``dotted_path`` resolves to a real field on the model."""
    resolved = reduce(
        lambda current, part: (
            _resolve_field(current, part) if current is not None else None
        ),
        dotted_path.split("."),
        model_cls,
    )
    return resolved is not None


class TestEnvMapSchemaSync:
    """GEOIPS_ENV_MAP must stay consistent with the schema."""

    @pytest.mark.parametrize("env_var,field_path", sorted(GEOIPS_ENV_MAP.items()))
    def test_env_map_value_resolves_to_field(self, env_var, field_path):
        """Every mapped dotted path must reference an actual GeoSettings field."""
        assert _field_path_is_valid(GeoSettings, field_path), (
            f"GEOIPS_ENV_MAP[{env_var!r}] -> {field_path!r} is not a valid "
            "GeoSettings field. Update GEOIPS_ENV_MAP or the schema."
        )

    def test_all_settings_have_env_var(self):
        """Every schema leaf field must be registered in GEOIPS_ENV_MAP.

        This prevents new settings from being added without a documented,
        trackable environment variable (or being explicitly listed as
        auto-derived).
        """
        mapped = set(GEOIPS_ENV_MAP.values())
        unmapped = _leaf_field_paths(GeoSettings) - mapped - AUTO_DERIVED_FIELDS
        assert not unmapped, (
            "The following settings are missing from GEOIPS_ENV_MAP (add an "
            f"env var mapping or list them as auto-derived): {sorted(unmapped)}"
        )


class TestEnvMapLegacyDictSync:
    """GEOIPS_ENV_MAP and the backward-compatible legacy dict must agree."""

    @pytest.fixture
    def legacy_keys(self, monkeypatch):
        """Return the set of keys exposed by the backward-compatible dict."""
        monkeypatch.setenv("GEOIPS_OUTDIRS", "/test/out")
        cfg = GeoIPSConfig()
        with pytest.warns(DeprecationWarning):
            return set(cfg.to_legacy_dict().keys())

    def test_legacy_keys_are_mapped_or_auto_derived(self, legacy_keys):
        """Every legacy dict key must be a known env var or auto-derived."""
        extra = legacy_keys - set(GEOIPS_ENV_MAP) - AUTO_DERIVED_LEGACY_KEYS
        assert not extra, (
            "Legacy dict exposes keys not present in GEOIPS_ENV_MAP (register "
            f"them or list them as auto-derived): {sorted(extra)}"
        )

    def test_mapped_env_vars_present_in_legacy_dict(self, legacy_keys):
        """Every non-alias env var must appear in the legacy dict."""
        missing = set(GEOIPS_ENV_MAP) - legacy_keys - ENV_VAR_ALIASES
        assert not missing, (
            "Env vars in GEOIPS_ENV_MAP are missing from the legacy dict "
            "(add them to _build_legacy_dict or mark as aliases): "
            f"{sorted(missing)}"
        )


def test_pydantic_available():
    """Sanity check that pydantic (schema dependency) is importable."""
    assert pydantic.VERSION
