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

    presectored_data: str = Field(
        "preprocessed/sectored", description="Pre-sectored intermediate data."
    )
    preread_data: str = Field(
        "preprocessed/unsectored", description="Pre-read (unsectored) data."
    )
    preregistered_data: str = Field(
        "preprocessed/registered", description="Pre-registered intermediate data."
    )
    precalculated_data: str = Field(
        "preprocessed/algorithms", description="Pre-calculated algorithm data."
    )
    clean_imagery: str = Field(
        "preprocessed/clean_imagery", description="Clean (unannotated) imagery."
    )
    annotated_imagery: str = Field(
        "preprocessed/annotated_imagery", description="Annotated imagery output."
    )
    geotiff_imagery: str = Field(
        "preprocessed/geotiff_imagery", description="GeoTIFF imagery output."
    )
    final_data: str = Field(
        "preprocessed/final", description="Final processed data output."
    )
    pregenerated_geolocation: str = Field(
        "preprocessed/geolocation", description="Pre-generated geolocation data."
    )
    scratch: str = Field("scratch", description="General scratch directory.")
    localscratch: str = Field("scratch", description="Node-local scratch directory.")
    sharedscratch: str = Field("scratch", description="Shared scratch directory.")
    logdir: str = Field("logs", description="Log file directory.")
    geoipsdata: str = Field("geoipsdata", description="Miscellaneous GeoIPS data.")
    ancildat_autogen: str = Field(
        "ancildat_autogen", description="Auto-generated ancillary data."
    )
    ancildat: str = Field("ancildat", description="Static ancillary data.")
    tcwww: str = Field("preprocessed/tcwww", description="TC web output.")
    tcprivatewww: str = Field(
        "preprocessed/tcprivatewww", description="Private TC web output."
    )
    publicwww: str = Field("preprocessed/publicwww", description="Public web output.")
    privatewww: str = Field(
        "preprocessed/privatewww", description="Private web output."
    )
    tc_decks_db: str = Field(
        "longterm_files/tc/tc_decks.db", description="TC decks database file."
    )
    tc_decks_dir: str = Field(
        "longterm_files/tc/decks", description="TC deck files directory."
    )


class CacheSettings(BaseModel):
    """Cache directory and backend configuration."""

    model_config = ConfigDict(frozen=True)

    cache_dir: str | None = Field(
        None, description="Base cache directory (defaults to the platform cache dir)."
    )
    data_cache_dir: str | None = Field(
        None, description="Data cache directory (defaults to cache_dir)."
    )
    satpy_data_cache_dir: str | None = Field(
        None, description="Satpy data cache directory (defaults to cache_dir)."
    )
    geolocation_cache_backend: str = Field(
        "memmap", description="Geolocation cache backend (e.g. 'memmap')."
    )
    data_cache_shortterm_geolocation_dynamic: str = Field(
        "shortterm/geolocation/dynamic",
        description="Short-term dynamic geolocation cache subpath.",
    )
    data_cache_longterm_geolocation_static: str = Field(
        "longterm/geolocation/static",
        description="Long-term static geolocation cache subpath.",
    )
    data_cache_shortterm_geolocation_solar_angles: str = Field(
        "shortterm/geolocation/solar",
        description="Short-term solar-angle geolocation cache subpath.",
    )
    data_cache_shortterm_calibrated_data: str = Field(
        "shortterm/calibrated_data",
        description="Short-term calibrated data cache subpath.",
    )
    satpy_cache_shortterm_calibrated_data: str = Field(
        "shortterm/calibrated_data",
        description="Short-term Satpy calibrated data cache subpath.",
    )
    satpy_cache_shortterm_geolocation_solar_angles: str = Field(
        "shortterm/geolocation/solar",
        description="Short-term Satpy solar-angle cache subpath.",
    )


class FeatureSettings(BaseModel):
    """Boolean feature toggles controlling GeoIPS behavior."""

    model_config = ConfigDict(frozen=True)

    no_color: bool = Field(False, description="Disable colored console output.")
    use_pydantic: bool = Field(
        False, description="Use pydantic-based plugin validation."
    )
    rebuild_registries: bool = Field(
        True, description="Rebuild plugin registries automatically when needed."
    )
    operational_user: bool = Field(
        False, description="Enable operational-user behavior."
    )
    rich_console_output: bool = Field(
        False, description="Enable rich-formatted console output."
    )


class LoggingSettings(BaseModel):
    """Logging format and level configuration."""

    model_config = ConfigDict(frozen=True)

    level: str = Field(
        "interactive", description="Logging level (interactive, info, debug, ...)."
    )
    fmt_string: str = Field(
        "%(asctime)s %(module)12s.py:%(lineno)-4d %(levelname)7s: %(message)s",
        description="Logging message format string.",
    )
    datefmt_string: str = Field("%d_%H%M%S", description="Logging date format string.")


class TestSettings(BaseModel):
    """Test-related configuration for output checking and comparison."""

    model_config = ConfigDict(frozen=True)

    output_checker_threshold_image: float = Field(
        0.05, description="Image comparison difference threshold."
    )
    print_text_output_checker_to_console: bool = Field(
        True, description="Print text output-checker diffs to the console."
    )
    prompt_to_overwrite_comparison_file_if_mismatch: bool = Field(
        False, description="Prompt to overwrite comparison files on mismatch."
    )
    suppress_pytest_failed_log_contents: bool = Field(
        False, description="Suppress log contents for failed pytest output."
    )
    sector_create_annotated_outputs: bool = Field(
        False, description="Create annotated outputs during sector tests."
    )
    sector_create_geotiff_outputs: bool = Field(
        False, description="Create GeoTIFF outputs during sector tests."
    )


class GeoSettings(BaseModel):
    """Root configuration model for all GeoIPS settings.

    Frozen (immutable) after creation. All values are validated against
    the declared types. Nested models isolate related config groups.

    The config loader resolves auto-derived paths (``basedir``,
    ``packages_dir``, ``cache_dir``, ``boxname``, output paths) at
    initialization time.
    """

    model_config = ConfigDict(frozen=True)

    outdirs: str = Field(description="Base directory for all GeoIPS output.")
    packages_dir: str | None = Field(
        None, description="Directory containing GeoIPS plugin packages."
    )
    basedir: str | None = Field(
        None, description="Base directory for the GeoIPS installation/source."
    )
    testdata_dir: str | None = Field(
        None, description="Directory containing GeoIPS test data."
    )
    dependencies_dir: str | None = Field(
        None, description="Directory for external dependencies."
    )
    base_path: str | None = Field(
        None, description="Path to the installed geoips package (auto-derived)."
    )

    output_paths: OutputPathsSettings = Field(
        default_factory=OutputPathsSettings, description="Output sub-directories."
    )
    cache: CacheSettings = Field(
        default_factory=CacheSettings, description="Cache directories and backend."
    )
    features: FeatureSettings = Field(
        default_factory=FeatureSettings, description="Boolean feature toggles."
    )
    logging: LoggingSettings = Field(
        default_factory=LoggingSettings, description="Logging configuration."
    )
    test: TestSettings = Field(
        default_factory=TestSettings, description="Test/comparison configuration."
    )

    version: str = Field("0.0.0", description="GeoIPS version string.")
    copyright: str = Field("NRL-Monterey", description="Copyright holder.")
    copyright_abbreviated: str = Field(
        "NRLMRY", description="Abbreviated copyright holder."
    )
    docs_url: str = Field(
        "https://nrlmmd-geoips.github.io/geoips/",
        description="URL for the GeoIPS documentation.",
    )
    rcfile: str = Field("", description="Path to a GeoIPS rc file, if any.")
    default_queue: str | None = Field(None, description="Default job scheduler queue.")
    boxname: str | None = Field(
        None, description="Hostname/box identifier (auto-derived)."
    )
    warning_level: str = Field("default", description="Python warnings filter level.")
    home: str | None = Field(None, description="Home directory (auto-derived).")

    replace_output_paths: list[str] = Field(
        default_factory=list,
        description="Path names to replace when building output filenames.",
    )
    pregenerated_static_geolocation: str = Field(
        "longterm_files/geolocation",
        description="Sub-path for pre-generated static geolocation.",
    )
    pregenerated_dynamic_geolocation: str = Field(
        "longterm_files/geolocation_dynamic",
        description="Sub-path for pre-generated dynamic geolocation.",
    )
    tc_decks_type: str = Field("bdecks", description="TC decks type (e.g. 'bdecks').")
    tc_template: str = Field(
        "plugins/yaml/sectors/dynamic/tc_web_template.yaml",
        description="Path to the TC web sector template.",
    )

    tcwww_url: str | None = Field(None, description="URL for TC web output.")
    tcprivatewww_url: str | None = Field(
        None, description="URL for private TC web output."
    )
    publicwww_url: str | None = Field(None, description="URL for public web output.")
    privatewww_url: str | None = Field(None, description="URL for private web output.")


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
"""Mapping from environment variable names to dotted model field paths.

Used by the config loader to apply env var overrides on top of the
settings model. Keys are environment variable names (with or without a
``GEOIPS_`` prefix), and values are dot-separated field paths into the
configuration model tree (e.g. ``features.no_color``).
"""
