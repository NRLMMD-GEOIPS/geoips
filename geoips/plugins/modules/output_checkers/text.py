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
from typing import Optional
from dataclasses import dataclass

from geoips.commandline.log_setup import log_with_emphasis
from geoips.geoips_utils import get_numpy_seeded_random_generator
from geoips.filenames.base_paths import PATHS

# Rich output configuration
USE_RICH = True  # Set this constant to control rich output

if USE_RICH:
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.text import Text
        from rich.syntax import Syntax
        from rich.table import Table
        from rich import box
        
        console = Console()
        RICH_AVAILABLE = True
    except ImportError:
        RICH_AVAILABLE = False
        USE_RICH = False
else:
    RICH_AVAILABLE = False

PRINT_TO_CONSOLE = PATHS["GEOIPS_TEST_PRINT_TEXT_OUTPUT_CHECKER_TO_CONSOLE"]

# Module constants
interface = "output_checkers"
family = "standard"
name = "text"

LOG = logging.getLogger(__name__)
predictable_random = get_numpy_seeded_random_generator()


@dataclass
class ComparisonResult:
    """Container for file comparison results."""
    matches: bool
    diff_output: str = ""


def _print_rich_success(message: str):
    """Print success message using rich formatting."""
    if USE_RICH and RICH_AVAILABLE:
        console.print(Panel(
            Text(message, style="bold green"),
            title="✅ Success",
            border_style="green",
            box=box.ROUNDED
        ))
    else:
        print(f"✅ {message}")


def _print_rich_error(title: str, *messages: str):
    """Print error messages using rich formatting."""
    if USE_RICH and RICH_AVAILABLE:
        content = Text()
        for i, msg in enumerate(messages):
            if i > 0:
                content.append("\n")
            content.append(msg, style="bold red" if i == 0 else "red")
        
        console.print(Panel(
            content,
            title="❌ Error",
            border_style="red",
            box=box.ROUNDED
        ))
    else:
        print(f"❌ {title}")
        for msg in messages:
            print(f"   {msg}")


def _print_rich_diff(diff_output: str, file1: str, file2: str):
    """Print diff output using rich formatting."""
    if USE_RICH and RICH_AVAILABLE:
        # Create a table for file comparison
        table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
        table.add_column("File 1", style="cyan")
        table.add_column("File 2", style="yellow")
        table.add_row(str(file1), str(file2))
        
        console.print(Panel(
            table,
            title="📁 Files Being Compared",
            border_style="blue"
        ))
        
        # Display diff output with syntax highlighting
        if diff_output.strip():
            try:
                syntax = Syntax(
                    diff_output,
                    "diff",
                    theme="monokai",
                    line_numbers=True,
                    word_wrap=True
                )
                console.print(Panel(
                    syntax,
                    title="🔍 Differences Found",
                    border_style="yellow",
                    box=box.ROUNDED
                ))
            except Exception:
                # Fallback to plain text if syntax highlighting fails
                console.print(Panel(
                    Text(diff_output, style="yellow"),
                    title="🔍 Differences Found",
                    border_style="yellow",
                    box=box.ROUNDED
                ))
    else:
        print(f"\n{'='*80}")
        print("DIFFERENCES FOUND:")
        print(f"File 1: {file1}")
        print(f"File 2: {file2}")
        print("=" * 80)
        print(diff_output)
        print(f"{'='*80}\n")


def correct_file_format(fname):
    """Check if file has a supported text format."""
    supported_extensions = {".txt", ".text", ".yaml", ".log", ""}
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
    """Execute diff command between two files."""
    try:
        result = subprocess.run(
            ["diff", str(file1), str(file2)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
        )
        return ComparisonResult(
            matches=(result.returncode == 0), 
            diff_output=result.stdout
        )
    except Exception as e:
        LOG.error(f"Diff operation failed: {e}")
        raise


def log_comparison_result(result, output_product, compare_product, diff_file=None):
    """Log comparison results with optional console output."""
    if result.matches:
        log_with_emphasis(LOG.info, "GOOD Text files match")
        if PRINT_TO_CONSOLE:
            _print_rich_success("Text files match perfectly!")
        return

    log_messages = [
        "BAD Text files do NOT match exactly",
        f"output_product: {output_product}",
        f"compare_product: {compare_product}",
    ]
    if diff_file:
        log_messages.append(f"out_difftxt: {diff_file}")

    log_with_emphasis(LOG.interactive, *log_messages)

    if PRINT_TO_CONSOLE:
        error_messages = [
            f"Output: {output_product}",
            f"Compare: {compare_product}"
        ]
        if diff_file:
            error_messages.append(f"Diff file: {diff_file}")
            
        _print_rich_error("Text files do NOT match exactly", *error_messages)
        
        if result.diff_output:
            _print_rich_diff(result.diff_output, output_product, compare_product)


def write_diff_file(file1, file2, output_file):
    """Write diff output to a file."""
    try:
        with Path(output_file).open("w", encoding="utf-8") as fobj:
            subprocess.call(["diff", str(file1), str(file2)], stdout=fobj, timeout=30)
    except Exception as e:
        LOG.error(f"Failed to write diff to {output_file}: {e}")
        raise


def outputs_match(plugin, output_product, compare_product):
    """Compare two text files for exact content match."""
    if not (correct_file_format(output_product) and correct_file_format(compare_product)):
        raise ValueError("Both files must be valid text files")

    result = run_diff(output_product, compare_product)
    LOG.debug(result.diff_output)

    diff_file = None
    if not result.matches:
        diff_file = plugin.get_out_diff_fname(compare_product, output_product)
        write_diff_file(output_product, compare_product, diff_file)

    log_comparison_result(result, output_product, compare_product, diff_file)
    return result.matches


def compare_text_files(output_product, compare_product):
    """Check if two text files match (convenience function)."""
    if not (correct_file_format(output_product) and correct_file_format(compare_product)):
        raise ValueError("Both files must be valid text files")
    
    result = run_diff(output_product, compare_product)
    LOG.debug(result.diff_output)
    
    if result.matches:
        log_with_emphasis(LOG.info, "GOOD Text files match")
        if PRINT_TO_CONSOLE:
            _print_rich_success("Text files match perfectly!")
    else:
        log_with_emphasis(
            LOG.interactive,
            "BAD Text files do NOT match exactly",
            f"output_product: {output_product}",
            f"compare_product: {compare_product}",
        )
        
        if PRINT_TO_CONSOLE:
            error_messages = [
                f"Output: {output_product}",
                f"Compare: {compare_product}"
            ]
            _print_rich_error("Text files do NOT match exactly", *error_messages)
            
            if result.diff_output:
                _print_rich_diff(result.diff_output, output_product, compare_product)
    
    return result.matches


def call(plugin, compare_path, output_products):
    """Execute comparison workflow for output validation."""
    return plugin.compare_outputs(compare_path, output_products)


# =============================================================================
# TESTING UTILITIES
# =============================================================================

def write_file_subset(lines, filename, percent_to_write, random_func=None):
    """Write a random subset of lines to a file."""
    if random_func is None:
        random_func = predictable_random.random

    threshold = (100 - percent_to_write) / 100

    with Path(filename).open("w", encoding="utf-8") as f:
        for line in lines:
            if random_func() > threshold:
                f.write(line)

    return str(filename)


def get_test_files(test_data_dir):
    """Generate test files with controlled similarity levels."""
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
    """Execute comparison tests and validate expected results."""
    if USE_RICH and RICH_AVAILABLE and PRINT_TO_CONSOLE:
        console.print(Panel(
            "Starting test comparisons...",
            title="🧪 Test Suite",
            border_style="blue"
        ))
    
    for idx, test_file in enumerate(test_files):
        result = outputs_match(plugin, test_file, compare_file)
        expected_match = idx == 0  # Only first file should match
        
        if USE_RICH and RICH_AVAILABLE and PRINT_TO_CONSOLE:
            status = "✅ PASS" if result == expected_match else "❌ FAIL"
            style = "green" if result == expected_match else "red"
            console.print(f"Test {idx + 1}: {status}", style=style)
        
        assert (
            result == expected_match
        ), f"Test {idx}: expected {expected_match}, got {result}"
    
    if USE_RICH and RICH_AVAILABLE and PRINT_TO_CONSOLE:
        console.print(Panel(
            "All tests completed successfully! 🎉",
            title="✅ Test Results",
            border_style="green"
        ))
