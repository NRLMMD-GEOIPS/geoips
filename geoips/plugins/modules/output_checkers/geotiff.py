"""Test script for representative product comparisons using GeoTIFF files."""

from __future__ import annotations

import logging
from functools import partial
from pathlib import Path
from typing import Sequence

import numpy as np
import rasterio
from rasterio.errors import RasterioIOError

from geoips.commandline.log_setup import log_with_emphasis

LOG = logging.getLogger(__name__)

interface = "output_checkers"
family = "standard"
name = "geotiff"

# Comparison configuration
COMPARISON_TOLERANCE = 1e-6
VALID_EXTENSIONS = frozenset({".tif", ".tiff", ".geotif", ".geotiff"})
IGNORED_METADATA_FIELDS = frozenset({"creation_timestamp", "datetime", "created"})
RANDOM_SEED = 42

# Test noise scales
CLOSE_MISMATCH_NOISE_SCALE = 0.05
BAD_MISMATCH_NOISE_SCALE = 0.25


def correct_file_format(fname: str) -> bool:
    """Determine if fname is a GeoTIFF file.

    Parameters
    ----------
    fname : str
        Name of file to check.

    Returns
    -------
    bool
        True if it is a GeoTIFF file, False otherwise.
    """
    return Path(fname).suffix.lower() in VALID_EXTENSIONS


def _validate_file_exists(filepath: Path) -> bool:
    """Validate that a file exists at the given path.

    Parameters
    ----------
    filepath : Path
        Path to validate.

    Returns
    -------
    bool
        True if file exists, False otherwise.
    """
    if not filepath.exists():
        LOG.error("File not found: %s", filepath)
        return False
    return True


def _filter_metadata(profile: dict) -> dict:
    """Filter out ignored fields from rasterio profile metadata.

    Parameters
    ----------
    profile : dict
        Rasterio profile dictionary.

    Returns
    -------
    dict
        Filtered profile with ignored fields removed.
    """
    return {
        key: value
        for key, value in profile.items()
        if key.lower() not in IGNORED_METADATA_FIELDS
    }


def _compare_metadata(output_profile: dict, compare_profile: dict) -> bool:
    """Compare two rasterio profiles, ignoring specified fields.

    Parameters
    ----------
    output_profile : dict
        Profile from output product.
    compare_profile : dict
        Profile from comparison product.

    Returns
    -------
    bool
        True if profiles match, False otherwise.
    """
    filtered_output = _filter_metadata(output_profile)
    filtered_compare = _filter_metadata(compare_profile)
    return filtered_output == filtered_compare


def _compare_arrays(output_data: np.ndarray, compare_data: np.ndarray) -> bool:
    """Compare two numpy arrays with appropriate tolerance for data type.

    Parameters
    ----------
    output_data : np.ndarray
        Array from output product.
    compare_data : np.ndarray
        Array from comparison product.

    Returns
    -------
    bool
        True if arrays match within tolerance, False otherwise.
    """
    if np.issubdtype(output_data.dtype, np.floating):
        return np.allclose(
            output_data,
            compare_data,
            rtol=COMPARISON_TOLERANCE,
            atol=COMPARISON_TOLERANCE,
            equal_nan=True,
        )
    return np.array_equal(output_data, compare_data)


def _calculate_difference_stats(
    output_data: np.ndarray, compare_data: np.ndarray
) -> tuple[float, float]:
    """Calculate difference statistics between two arrays.

    Parameters
    ----------
    output_data : np.ndarray
        Array from output product.
    compare_data : np.ndarray
        Array from comparison product.

    Returns
    -------
    tuple[float, float]
        Maximum difference and mean difference.
    """
    diff = np.abs(output_data.astype(np.float64) - compare_data.astype(np.float64))
    return float(np.max(diff)), float(np.mean(diff))


def _log_mismatch(
    message: str,
    output_product: str,
    compare_product: str,
    additional_info: Sequence[str] = (),
) -> None:
    """Log a mismatch between two products.

    Parameters
    ----------
    message : str
        Main message describing the mismatch.
    output_product : str
        Path to output product.
    compare_product : str
        Path to comparison product.
    additional_info : Sequence[str], optional
        Additional information to log.
    """
    log_with_emphasis(
        LOG.interactive,
        message,
        f"output_product: {output_product}",
        f"compare_product: {compare_product}",
        *additional_info,
    )


def _read_geotiff(filepath: Path) -> tuple[np.ndarray, dict]:
    """Read data and profile from a GeoTIFF file.

    Parameters
    ----------
    filepath : Path
        Path to GeoTIFF file.

    Returns
    -------
    tuple[np.ndarray, dict]
        Tuple of (raster data, profile dictionary).
    """
    with rasterio.open(filepath) as src:
        return src.read(), dict(src.profile)


def _write_geotiff(filepath: Path, data: np.ndarray, profile: dict) -> None:
    """Write data to a GeoTIFF file.

    Parameters
    ----------
    filepath : Path
        Path to output GeoTIFF file.
    data : np.ndarray
        Raster data to write.
    profile : dict
        Rasterio profile dictionary.
    """
    with rasterio.open(filepath, "w", **profile) as dst:
        dst.write(data)


def _create_noisy_data(
    data: np.ndarray, scale: float, rng: np.random.Generator
) -> np.ndarray:
    """Create a copy of data with added Gaussian noise.

    Parameters
    ----------
    data : np.ndarray
        Original raster data.
    scale : float
        Standard deviation of the Gaussian noise.
    rng : np.random.Generator
        Random number generator.

    Returns
    -------
    np.ndarray
        Data with added noise.
    """
    noise = rng.normal(scale=scale, size=data.shape)
    return data + noise


def outputs_match(plugin, output_product: str, compare_product: str) -> bool:
    """Compare two GeoTIFF files for equality.

    Parameters
    ----------
    plugin : OutputCheckerPlugin
        The corresponding GeoTIFF output checker (required for API compatibility).
    output_product : str
        Full path to current output product.
    compare_product : str
        Full path to comparison product.

    Returns
    -------
    bool
        True if images match within tolerance, False if they differ.
    """
    output_path = Path(output_product)
    compare_path = Path(compare_product)

    if not all(map(_validate_file_exists, (output_path, compare_path))):
        return False

    try:
        output_data, output_profile = _read_geotiff(output_path)
        compare_data, compare_profile = _read_geotiff(compare_path)

        if not _compare_metadata(output_profile, compare_profile):
            _log_mismatch(
                "BAD GeoTIFFs metadata does NOT match",
                output_product,
                compare_product,
            )
            return False

        if not _compare_arrays(output_data, compare_data):
            max_diff, mean_diff = _calculate_difference_stats(output_data, compare_data)
            _log_mismatch(
                "BAD GeoTIFFs do NOT match",
                output_product,
                compare_product,
                (f"max_diff: {max_diff}", f"mean_diff: {mean_diff}"),
            )
            return False

        log_with_emphasis(LOG.info, "GOOD GeoTIFFs match")
        return True

    except RasterioIOError as e:
        LOG.error("Error reading GeoTIFF files: %s", e)
        return False


def call(plugin, compare_path: str, output_products: list[str]) -> int:
    """Compare correct GeoTIFFs with current output products.

    Compares files produced in the current processing run with the list of
    correct files contained in compare_path.

    Parameters
    ----------
    plugin : OutputCheckerPlugin
        The corresponding GeoTIFF OutputCheckerPlugin.
    compare_path : str
        Path to directory of correct products.
    output_products : list[str]
        List of current output products to compare.

    Returns
    -------
    int
        Binary code: 0 if all comparisons were completed successfully.
    """
    return plugin.compare_outputs(compare_path, output_products)


def _setup_test_directory(test_data_dir: str) -> Path:
    """Create and return the test directory path.

    Parameters
    ----------
    test_data_dir : str
        Base test data directory.

    Returns
    -------
    Path
        Path to the test GeoTIFFs directory.
    """
    savedir = Path(test_data_dir) / "scratch" / "unit_tests" / "test_geotiffs"
    savedir.mkdir(parents=True, exist_ok=True)
    return savedir


def _get_source_tiff_path() -> Path:
    """Get the path to the source test GeoTIFF file.

    Returns
    -------
    Path
        Path to the source GeoTIFF file.
    """
    from importlib.resources import files

    tif_name = "20200405_000000_SH252020_ahi_himawari-8_WV_100kts_100p00_1p0.tif"
    return Path(str(files("geoips") / "../tests/outputs/ahi.tc.WV.geotiff" / tif_name))


def _generate_test_files(
    savedir: Path,
    compare_data: np.ndarray,
    profile: dict,
    rng: np.random.Generator,
) -> tuple[Path, list[Path]]:
    """Generate test GeoTIFF files with various modifications.

    Parameters
    ----------
    savedir : Path
        Directory to save test files.
    compare_data : np.ndarray
        Original comparison data.
    profile : dict
        Rasterio profile for writing files.
    rng : np.random.Generator
        Random number generator.

    Returns
    -------
    tuple[Path, list[Path]]
        Tuple of (compare_file, [matched_file, close_mismatch_file, bad_mismatch_file]).
    """
    file_specs = [
        ("compare.tif", lambda d: d),
        ("matched.tif", lambda d: d),
        (
            "close_mismatch.tif",
            partial(_create_noisy_data, scale=CLOSE_MISMATCH_NOISE_SCALE, rng=rng),
        ),
        (
            "bad_mismatch.tif",
            partial(_create_noisy_data, scale=BAD_MISMATCH_NOISE_SCALE, rng=rng),
        ),
    ]

    generated_paths = []
    for filename, transform in file_specs:
        filepath = savedir / filename
        transformed_data = transform(compare_data)
        _write_geotiff(filepath, transformed_data, profile)
        generated_paths.append(filepath)

    compare_file, *test_files = generated_paths
    return compare_file, test_files


def get_test_files_long(test_data_dir: str) -> tuple[str, list[str]]:
    """Generate a series of GeoTIFF paths for testing comparisons.

    Creates a compare file and test files with varying degrees of modification
    for testing the output checker functionality.

    Parameters
    ----------
    test_data_dir : str
        Base directory for test data.

    Returns
    -------
    tuple[str, list[str]]
        Tuple of (compare_file_path, [matched, close_mismatch, bad_mismatch]).
    """
    import shutil

    rng = np.random.default_rng(RANDOM_SEED)
    savedir = _setup_test_directory(test_data_dir)
    source_path = _get_source_tiff_path()

    temp_compare = savedir / "compare.tif"
    shutil.copy(source_path, temp_compare)

    compare_data, profile = _read_geotiff(temp_compare)
    compare_file, test_files = _generate_test_files(savedir, compare_data, profile, rng)

    return str(compare_file), [str(path) for path in test_files]


def perform_test_comparisons_long(
    plugin, compare_file: str, test_files: list[str]
) -> None:
    """Test comparison of GeoTIFF files with the GeoTIFF Output Checker.

    Parameters
    ----------
    plugin : OutputCheckerPlugin
        The GeoTIFF output checker plugin.
    compare_file : str
        Path to the comparison (baseline) file.
    test_files : list[str]
        List of test file paths [matched, close_mismatch, bad_mismatch].

    Raises
    ------
    AssertionError
        If any comparison result doesn't match expected outcome.
    """
    expected_results = [True, False, False]

    comparison_results = [
        plugin.module.outputs_match(plugin, test_file, compare_file)
        for test_file in test_files
    ]

    for test_file, result, expected in zip(
        test_files, comparison_results, expected_results
    ):
        assert result is expected, (
            f"Unexpected comparison result for {test_file}: "
            f"got {result}, expected {expected}"
        )
