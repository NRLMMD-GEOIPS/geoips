# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Text file comparison utilities for output validation.

This module provides functionality to compare text files and validate their formats,
primarily used for testing output consistency in the GeoIPS system.
"""

import subprocess
import logging
from pathlib import Path
from shutil import copy
from importlib.resources import files
from typing import List, Tuple, Optional
from dataclasses import dataclass

from geoips.commandline.log_setup import log_with_emphasis
from geoips.geoips_utils import get_numpy_seeded_random_generator
from geoips.filenames.base_paths import PATHS

PRINT_TO_CONSOLE = PATHS["GEOIPS_TEST_PRINT_TEXT_OUTPUT_CHECKER_TO_CONSOLE"]

# Module constants
interface = "output_checkers"
family = "standard"
name = "text"

LOG = logging.getLogger(__name__)
predictable_random = get_numpy_seeded_random_generator()


@dataclass
class ComparisonResult:
    """Container for file comparison results.

    Attributes
    ----------
    matches : bool
        True if files are identical, False otherwise.
    diff_output : str, default=""
        Unified diff output showing differences between files.

    Examples
    --------
    >>> result = ComparisonResult(matches=True)
    >>> result.matches
    True
    >>> result.diff_output
    ''
    """

    matches: bool
    diff_output: str = ""


def is_text_file(fname):
    """Validate if a file is a supported text format.

    Tests file extension and attempts to read the first line to verify
    the file contains readable text content.

    Parameters
    ----------
    fname : str or Path
        Path to file for validation.

    Returns
    -------
    bool
        True if file has supported extension and is readable as text.

    Examples
    --------
    >>> import tempfile
    >>> with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
    ...     _ = f.write('test content')
    ...     temp_path = f.name
    >>> is_text_file(temp_path)
    True
    >>> Path(temp_path).unlink()  # cleanup

    >>> is_text_file('nonexistent.bin')
    False
    """
    supported_extensions = {"", ".txt", ".text", ".yaml", ".log"}
    file_path = Path(fname)

    if file_path.suffix not in supported_extensions:
        return False

    try:
        with file_path.open("r", encoding="utf-8") as f:
            f.readline()
        return True
    except (UnicodeDecodeError, IOError):
        return False


def run_diff(file1, file2):
    """Execute diff command between two files.

    Uses system diff utility to compare files and capture output.
    Includes 30-second timeout to prevent hanging on large files.

    Parameters
    ----------
    file1 : str or Path
        Path to first file for comparison.
    file2 : str or Path
        Path to second file for comparison.

    Returns
    -------
    ComparisonResult
        Result object containing match status and diff output.

    Raises
    ------
    subprocess.TimeoutExpired
        If diff operation exceeds 30 seconds.
    FileNotFoundError
        If either input file does not exist.
    """
    try:
        result = subprocess.run(
            ["diff", str(file1), str(file2)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
        )
        return ComparisonResult(
            matches=(result.returncode == 0), diff_output=result.stdout
        )
    except Exception as e:
        LOG.error(f"Diff operation failed: {e}")
        raise


def log_comparison_result(result, output_product, compare_product, diff_file=None):
    """Log comparison results and optionally print to console.

    Outputs success message for matching files or detailed failure information
    for non-matching files. Console output controlled by PRINT_TO_CONSOLE setting.

    Parameters
    ----------
    result : ComparisonResult
        Comparison result containing match status and diff output.
    output_product : str
        Path to the generated output file being tested.
    compare_product : str
        Path to the reference file for comparison.
    diff_file : str, optional
        Path to file where diff output was written.
    """
    if result.matches:
        log_with_emphasis(LOG.info, "GOOD Text files match")
        return

    # Log failure details
    log_messages = [
        "BAD Text files do NOT match exactly",
        f"output_product: {output_product}",
        f"compare_product: {compare_product}",
    ]
    if diff_file:
        log_messages.append(f"out_difftxt: {diff_file}")

    log_with_emphasis(LOG.interactive, *log_messages)

    # Print to console if enabled
    if PRINT_TO_CONSOLE and result.diff_output:
        print(f"\n{'='*80}")
        print("DIFFERENCES FOUND:")
        print("=" * 80)
        print(result.diff_output)
        print(f"{'='*80}\n")


def write_diff_file(file1, file2, output_file):
    """Write diff output to a file.

    Executes diff command and redirects output to specified file.
    Includes timeout protection for large file comparisons.

    Parameters
    ----------
    file1 : str or Path
        Path to first file for comparison.
    file2 : str or Path
        Path to second file for comparison.
    output_file : str or Path
        Path where diff output will be written.

    Raises
    ------
    subprocess.TimeoutExpired
        If diff operation exceeds 30 seconds.
    IOError
        If output file cannot be written.
    """
    try:
        with Path(output_file).open("w", encoding="utf-8") as fobj:
            subprocess.call(["diff", str(file1), str(file2)], stdout=fobj, timeout=30)
    except Exception as e:
        LOG.error(f"Failed to write diff to {output_file}: {e}")
        raise


def write_file_subset(lines, filename, percent_to_write, random_func=None):
    """Write a random subset of lines to a file.

    Selects lines probabilistically based on specified percentage.
    Uses seeded random generator for reproducible results.

    Parameters
    ----------
    lines : list of str
        Source lines to potentially write to file.
    filename : str or Path
        Destination file path.
    percent_to_write : int
        Percentage of lines to include (0-100).
    random_func : callable, optional
        Random number generator function. Defaults to seeded generator.

    Returns
    -------
    str
        Path to the created file.
    """
    if random_func is None:
        random_func = predictable_random.random

    threshold = (100 - percent_to_write) / 100

    with Path(filename).open("w", encoding="utf-8") as f:
        for line in lines:
            if random_func() > threshold:
                f.write(line)

    return str(filename)


def outputs_match(plugin, output_product, compare_product):
    """Compare two text files for exact content match.

    Validates file formats, performs diff comparison, and generates
    detailed output including diff files for mismatches.

    Parameters
    ----------
    plugin : OutputCheckerPlugin
        Plugin instance providing diff filename generation method.
    output_product : str
        Path to generated output file being validated.
    compare_product : str
        Path to reference file for comparison.

    Returns
    -------
    bool
        True if files have identical content, False otherwise.

    Raises
    ------
    ValueError
        If either file is not a valid text file format.
    """
    if not (is_text_file(output_product) and is_text_file(compare_product)):
        raise ValueError("Both files must be valid text files")

    result = run_diff(output_product, compare_product)
    LOG.debug(result.diff_output)

    diff_file = None
    if not result.matches:
        diff_file = plugin.get_out_diff_fname(compare_product, output_product)
        write_diff_file(output_product, compare_product, diff_file)

    log_comparison_result(result, output_product, compare_product, diff_file)
    return result.matches


def get_test_files(test_data_dir):
    """Generate test files with controlled similarity levels.

    Creates a reference file and three test files with 100%, 95%, and 75%
    line similarity for testing comparison functionality.

    Parameters
    ----------
    test_data_dir : str or Path
        Base directory for creating test file structure.

    Returns
    -------
    tuple of (str, list of str)
        Reference file path and list of test file paths.
    """
    save_dir = Path(test_data_dir) / "scratch" / "unit_tests" / "test_text"
    save_dir.mkdir(parents=True, exist_ok=True)

    # Copy source file
    text_path = files("geoips") / "plugins/txt/ascii_palettes/tpw_cimss.txt"
    comp_path = save_dir / "compare.txt"
    copy(str(text_path), str(comp_path))

    # Read content once
    with comp_path.open("r", encoding="utf-8") as f:
        content = f.readlines()

    # Create test files with different similarity levels
    test_configs = [
        ("matched.txt", 100),  # Should match exactly
        ("slightly_mismatch.txt", 95),  # Should not match
        ("bad_mismatch.txt", 75),  # Should not match
    ]

    test_files = [
        write_file_subset(content, str(save_dir / filename), percent)
        for filename, percent in test_configs
    ]

    return str(comp_path), test_files


def perform_test_comparisons(plugin, compare_file, test_files):
    """Execute comparison tests and validate expected results.

    Tests file comparison functionality using files with known similarity levels.
    Asserts that only the identical file (100% match) returns True.

    Parameters
    ----------
    plugin : OutputCheckerPlugin
        Plugin instance for performing comparisons.
    compare_file : str
        Path to reference file for comparisons.
    test_files : list of str
        List of test file paths in order: [exact_match, partial_match1, partial_match2].

    Raises
    ------
    AssertionError
        If comparison results don't match expected outcomes.

    Examples
    --------
    >>> from unittest.mock import Mock
    >>> plugin = Mock()
    >>> plugin.get_out_diff_fname.return_value = 'test_diff.txt'
    >>> # This would typically use real test files
    >>> # perform_test_comparisons(plugin, 'ref.txt', ['match.txt', 'diff1.txt', 'diff2.txt'])
    """
    for idx, test_file in enumerate(test_files):
        result = outputs_match(plugin, test_file, compare_file)
        expected_match = idx == 0  # Only first file should match
        assert (
            result == expected_match
        ), f"Test {idx}: expected {expected_match}, got {result}"


def call(plugin, compare_path, output_products):
    """Execute comparison workflow for output validation.

    Primary entry point for comparing generated outputs against reference files.
    Delegates to plugin's comparison implementation.

    Parameters
    ----------
    plugin : OutputCheckerPlugin
        Plugin instance containing comparison logic.
    compare_path : str
        Path to directory containing reference files.
    output_products : list of str
        List of generated output file paths to validate.

    Returns
    -------
    int
        Exit code: 0 for successful completion, non-zero for errors.
    """
    return int(plugin.outputs_match(compare_path, output_products))
