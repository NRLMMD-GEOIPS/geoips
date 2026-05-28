# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Pydantic schema models for GeoIPS configuration.

Defines the structure, types, and defaults for all GeoIPS configuration
values. Models are frozen (immutable) to prevent accidental mutation.
"""

from pydantic import BaseModel, ConfigDict, Field


class OutputPathsSettings(BaseModel):
    """Sub-paths for data output directories.

    Defaults are relative to ``outdirs``. The config loader resolves
    relative paths to absolute at initialization time. Environment
    variables or project YAML may override with absolute paths.
    """

    model_config = ConfigDict(frozen=True)

    presectored_data: str = "preprocessed/sectored"
    preread_data: str = "preprocessed/unsectored"
    preregistered_data: str = "preprocessed/registered"
    precalculated_data: str = "preprocessed/algorithms"
    clean_imagery: str = "preprocessed/clean_imagery"
    annotated_imagery: str = "preprocessed/annotated_imagery"
    geotiff_imagery: str = "preprocessed/geotiff_imagery"
    final_data: str = "preprocessed/final"
    pregenerated_geolocation: str = "preprocessed/geolocation"
    scratch: str = "scratch"
    localscratch: str = "scratch"
    sharedscratch: str = "scratch"
    logdir: str = "logs"
    geoipsdata: str = "geoipsdata"
    ancildat_autogen: str = "ancildat_autogen"
    ancildat: str = "ancildat"
    tcwww: str = "preprocessed/tcwww"
    tcprivatewww: str = "preprocessed/tcprivatewww"
    publicwww: str = "preprocessed/publicwww"
    privatewww: str = "preprocessed/privatewww"
    tc_decks_db: str = "longterm_files/tc/tc_decks.db"
    tc_decks_dir: str = "longterm_files/tc/decks"


class CacheSettings(BaseModel):
    """Cache directory and backend configuration."""

    model_config = ConfigDict(frozen=True)

    cache_dir: str | None = None
    data_cache_dir: str | None = None
    satpy_data_cache_dir: str | None = None
    geolocation_cache_backend: str = "memmap"
    data_cache_shortterm_geolocation_dynamic: str = "shortterm/geolocation/dynamic"
    data_cache_longterm_geolocation_static: str = "longterm/geolocation/static"
    data_cache_shortterm_geolocation_solar_angles: str = "shortterm/geolocation/solar"
    data_cache_shortterm_calibrated_data: str = "shortterm/calibrated_data"
    satpy_cache_shortterm_calibrated_data: str = "shortterm/calibrated_data"
    satpy_cache_shortterm_geolocation_solar_angles: str = "shortterm/geolocation/solar"


class FeatureSettings(BaseModel):
    """Boolean feature toggles controlling GeoIPS behavior."""

    model_config = ConfigDict(frozen=True)

    no_color: bool = False
    use_pydantic: bool = False
    rebuild_registries: bool = True
    operational_user: bool = False
    rich_console_output: bool = False


class LoggingSettings(BaseModel):
    """Logging format and level configuration."""

    model_config = ConfigDict(frozen=True)

    level: str = "interactive"
    fmt_string: str = (
        "%(asctime)s %(module)12s.py:%(lineno)-4d %(levelname)7s: %(message)s"
    )
    datefmt_string: str = "%d_%H%M%S"


class TestSettings(BaseModel):
    """Test-related configuration for output checking and comparison."""

    model_config = ConfigDict(frozen=True)

    output_checker_threshold_image: float = 0.05
    print_text_output_checker_to_console: bool = True
    prompt_to_overwrite_comparison_file_if_mismatch: bool = False
    suppress_pytest_failed_log_contents: bool = False
    sector_create_annotated_outputs: bool = False
    sector_create_geotiff_outputs: bool = False


class GeoSettings(BaseModel):
    """Root configuration model for all GeoIPS settings.

    Frozen (immutable) after creation. All values are validated against
    the declared types. Nested models isolate related config groups.

    The config loader resolves auto-derived paths (``basedir``,
    ``packages_dir``, ``cache_dir``, ``boxname``, output paths) at
    initialization time.
    """

    model_config = ConfigDict(frozen=True)

    outdirs: str
    packages_dir: str | None = None
    basedir: str | None = None
    testdata_dir: str | None = None
    dependencies_dir: str | None = None
    base_path: str | None = None

    output_paths: OutputPathsSettings = Field(default_factory=OutputPathsSettings)
    cache: CacheSettings = Field(default_factory=CacheSettings)
    features: FeatureSettings = Field(default_factory=FeatureSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    test: TestSettings = Field(default_factory=TestSettings)

    version: str = "0.0.0"
    copyright: str = "NRL-Monterey"
    copyright_abbreviated: str = "NRLMRY"
    docs_url: str = "https://nrlmmd-geoips.github.io/geoips/"
    rcfile: str = ""
    default_queue: str | None = None
    boxname: str | None = None
    warning_level: str = "default"
    home: str | None = None

    replace_output_paths: list[str] = Field(default_factory=list)
    pregenerated_static_geolocation: str = "longterm_files/geolocation"
    pregenerated_dynamic_geolocation: str = "longterm_files/geolocation_dynamic"
    tc_decks_type: str = "bdecks"
    tc_template: str = "plugins/yaml/sectors/dynamic/tc_web_template.yaml"

    tcwww_url: str | None = None
    tcprivatewww_url: str | None = None
    publicwww_url: str | None = None
    privatewww_url: str | None = None


GEOIPS_ENV_MAP: dict[str, str] = {
    "GEOIPS_OUTDIRS": "outdirs",
    "GEOIPS_PACKAGES_DIR": "packages_dir",
    "GEOIPS_BASEDIR": "basedir",
    "GEOIPS_TESTDATA_DIR": "testdata_dir",
    "GEOIPS_DEPENDENCIES_DIR": "dependencies_dir",
    "GEOIPS_CACHE_DIR": "cache.cache_dir",
    "GEOIPS_DATA_CACHE_DIR": "cache.data_cache_dir",
    "SATPY_DATA_CACHE_DIR": "cache.satpy_data_cache_dir",
    "GEOIPS_GEOLOCATION_CACHE_BACKEND": "cache.geolocation_cache_backend",
    "GEOIPS_DATA_CACHE_DIR_SHORTTERM_GEOLOCATION_DYNAMIC": (
        "cache.data_cache_shortterm_geolocation_dynamic"
    ),
    "GEOIPS_DATA_CACHE_DIR_LONGTERM_GEOLOCATION_STATIC": (
        "cache.data_cache_longterm_geolocation_static"
    ),
    "GEOIPS_DATA_CACHE_DIR_SHORTTERM_GEOLOCATION_SOLAR_ANGLES": (
        "cache.data_cache_shortterm_geolocation_solar_angles"
    ),
    "GEOIPS_DATA_CACHE_DIR_SHORTTERM_CALIBRATED_DATA": (
        "cache.data_cache_shortterm_calibrated_data"
    ),
    "SATPY_DATA_CACHE_DIR_SHORTTERM_CALIBRATED_DATA": (
        "cache.satpy_cache_shortterm_calibrated_data"
    ),
    "SATPY_DATA_CACHE_DIR_SHORTTERM_GEOLOCATION_SOLAR_ANGLES": (
        "cache.satpy_cache_shortterm_geolocation_solar_angles"
    ),
    "GEOIPS_NO_COLOR": "features.no_color",
    "NO_COLOR": "features.no_color",
    "GEOIPS_USE_PYDANTIC": "features.use_pydantic",
    "GEOIPS_REBUILD_REGISTRIES": "features.rebuild_registries",
    "GEOIPS_OPERATIONAL_USER": "features.operational_user",
    "GEOIPS_RICH_CONSOLE_OUTPUT": "features.rich_console_output",
    "GEOIPS_LOGGING_LEVEL": "logging.level",
    "GEOIPS_LOGGING_FMT_STRING": "logging.fmt_string",
    "GEOIPS_LOGGING_DATEFMT_STRING": "logging.datefmt_string",
    "GEOIPS_WARNING_LEVEL": "warning_level",
    "GEOIPS_TEST_OUTPUT_CHECKER_THRESHOLD_IMAGE": (
        "test.output_checker_threshold_image"
    ),
    "GEOIPS_TEST_PRINT_TEXT_OUTPUT_CHECKER_TO_CONSOLE": (
        "test.print_text_output_checker_to_console"
    ),
    "GEOIPS_TEST_PROMPT_TO_OVERWRITE_COMPARISON_FILE_IF_MISMATCH": (
        "test.prompt_to_overwrite_comparison_file_if_mismatch"
    ),
    "GEOIPS_TEST_SUPPRESS_PYTEST_FAILED_LOG_CONTENTS": (
        "test.suppress_pytest_failed_log_contents"
    ),
    "GEOIPS_TEST_SECTOR_CREATE_ANNOTATED_OUTPUTS": (
        "test.sector_create_annotated_outputs"
    ),
    "GEOIPS_TEST_SECTOR_CREATE_GEOTIFF_OUTPUTS": ("test.sector_create_geotiff_outputs"),
    "GEOIPS_VERSION": "version",
    "GEOIPS_COPYRIGHT": "copyright",
    "GEOIPS_COPYRIGHT_ABBREVIATED": "copyright_abbreviated",
    "GEOIPS_DOCS_URL": "docs_url",
    "GEOIPS_RCFILE": "rcfile",
    "DEFAULT_QUEUE": "default_queue",
    "BOXNAME": "boxname",
    "GEOIPS_REPLACE_OUTPUT_PATHS": "replace_output_paths",
    "GEOIPS_PREGENERATED_STATIC_GEOLOCATION": "pregenerated_static_geolocation",
    "GEOIPS_PREGENERATED_DYNAMIC_GEOLOCATION": ("pregenerated_dynamic_geolocation"),
    "GEOIPS_TC_DECKS_TYPE": "tc_decks_type",
    "GEOIPS_TC_DECKS_DB": "output_paths.tc_decks_db",
    "GEOIPS_TC_DECKS_DIR": "output_paths.tc_decks_dir",
    "GEOIPS_ANCILDAT_AUTOGEN": "output_paths.ancildat_autogen",
    "GEOIPS_ANCILDAT": "output_paths.ancildat",
    "PRESECTORED_DATA_PATH": "output_paths.presectored_data",
    "PREREAD_DATA_PATH": "output_paths.preread_data",
    "PREREGISTERED_DATA_PATH": "output_paths.preregistered_data",
    "PRECALCULATED_DATA_PATH": "output_paths.precalculated_data",
    "CLEAN_IMAGERY_PATH": "output_paths.clean_imagery",
    "ANNOTATED_IMAGERY_PATH": "output_paths.annotated_imagery",
    "GEOTIFF_IMAGERY_PATH": "output_paths.geotiff_imagery",
    "FINAL_DATA_PATH": "output_paths.final_data",
    "PREGENERATED_GEOLOCATION_PATH": "output_paths.pregenerated_geolocation",
    "SCRATCH": "output_paths.scratch",
    "LOCALSCRATCH": "output_paths.localscratch",
    "SHAREDSCRATCH": "output_paths.sharedscratch",
    "LOGDIR": "output_paths.logdir",
    "GEOIPSDATA": "output_paths.geoipsdata",
    "TCWWW": "output_paths.tcwww",
    "TCPRIVATEWWW": "output_paths.tcprivatewww",
    "PUBLICWWW": "output_paths.publicwww",
    "PRIVATEWWW": "output_paths.privatewww",
    "TCWWW_URL": "tcwww_url",
    "TCPRIVATEWWW_URL": "tcprivatewww_url",
    "PUBLICWWW_URL": "publicwww_url",
    "PRIVATEWWW_URL": "privatewww_url",
    "TC_TEMPLATE": "tc_template",
}
"""Mapping of environment variable names to dotted pydantic field paths.

Used by the config loader to apply env var overrides onto the GeoSettings model.
Keys are env var names (with or without GEOIPS_ prefix), values are dot-separated
paths into the GeoSettings model tree (e.g. ``features.no_color``).
"""
