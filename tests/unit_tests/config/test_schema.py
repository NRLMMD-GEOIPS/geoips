# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Tests for ``geoips.config.schema`` pydantic models."""

import pytest
from pydantic import ValidationError

from geoips.config.schema import (
    CacheSettings,
    FeatureSettings,
    GeoSettings,
    LoggingSettings,
    OutputPathsSettings,
    TestSettings,
)


class TestOutputPathsSettings:
    """Tests for OutputPathsSettings nested model."""

    def test_defaults(self):
        """Verify default values for all output path fields."""
        model = OutputPathsSettings()
        assert model.presectored_data == "preprocessed/sectored"
        assert model.scratch == "scratch"
        assert model.logdir == "logs"

    def test_frozen(self):
        """Verify the model is frozen and rejects mutation."""
        model = OutputPathsSettings()
        with pytest.raises(ValidationError):
            model.scratch = "different"


class TestCacheSettings:
    """Tests for CacheSettings nested model."""

    def test_defaults(self):
        """Verify default cache settings."""
        model = CacheSettings()
        assert model.geolocation_cache_backend == "memmap"
        assert model.cache_dir is None

    def test_can_set_fields(self):
        """Verify fields can be set via constructor."""
        model = CacheSettings(cache_dir="/custom/cache")
        assert model.cache_dir == "/custom/cache"


class TestFeatureSettings:
    """Tests for FeatureSettings nested model."""

    def test_defaults(self):
        """Verify default feature toggles."""
        model = FeatureSettings()
        assert model.no_color is False
        assert model.use_pydantic is False
        assert model.rebuild_registries is True

    def test_frozen(self):
        """Verify the model is frozen."""
        model = FeatureSettings()
        with pytest.raises(ValidationError):
            model.no_color = True


class TestLoggingSettings:
    """Tests for LoggingSettings nested model."""

    def test_defaults(self):
        """Verify default logging settings."""
        model = LoggingSettings()
        assert model.level == "interactive"
        assert "asctime" in model.fmt_string


class TestTestSettings:
    """Tests for TestSettings nested model."""

    def test_defaults(self):
        """Verify default test settings."""
        model = TestSettings()
        assert model.output_checker_threshold_image == 0.05
        assert model.print_text_output_checker_to_console is True


class TestGeoSettings:
    """Tests for the root GeoSettings model."""

    def test_requires_outdirs(self):
        """Verify GeoSettings requires outdirs field."""
        with pytest.raises(ValidationError):
            GeoSettings()

    @pytest.fixture(autouse=True)
    def _set_outdirs(self, tmp_path):
        self._outdirs = str(tmp_path / "out")

    def test_creates_nested_models_by_default(self):
        """Verify nested models are created with defaults."""
        model = GeoSettings(outdirs=self._outdirs)
        assert model.features.no_color is False
        assert model.output_paths.presectored_data == "preprocessed/sectored"
        assert model.cache.geolocation_cache_backend == "memmap"

    def test_frozen(self):
        """Verify root model is frozen."""
        model = GeoSettings(outdirs=self._outdirs)
        with pytest.raises(ValidationError):
            model.outdirs = "/changed"

    def test_nested_frozen(self):
        """Verify nested models are also frozen."""
        model = GeoSettings(outdirs=self._outdirs)
        with pytest.raises(ValidationError):
            model.features.no_color = True

    def test_metadata_defaults(self):
        """Verify default metadata values."""
        model = GeoSettings(outdirs=self._outdirs)
        assert model.version == "0.0.0"
        assert model.copyright == "NRL-Monterey"
        assert model.docs_url.startswith("https://")
