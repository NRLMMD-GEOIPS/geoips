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
from dataclasses import dataclass

from geoips.commandline.log_setup import log_with_emphasis
from geoips.geoips_utils import get_numpy_seeded_random_generator
from geoips.filenames.base_paths import PATHS

USE_RICH = PATHS["GEOIPS_RICH_CONSOLE_OUTPUT"]
PRINT_TO_CONSOLE = PATHS["GEOIPS_TEST_PRINT_TEXT_OUTPUT_CHECKER_TO_CONSOLE"]
PROMPT_TO_OVERWRITE_COMPARISON_FILE = PATHS.get(
    "GEOIPS_PROMPT_TO_OVERWRITE_COMPARISON_FILE_IF_MISMATCH", False
)

interface = "output_checkers"
family = "standard"
name = "text"

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

LOG = logging.getLogger(__name__)


@dataclass
class ComparisonResult:
    """Container for file comparison results."""

    matches: bool
    diff_output: str = ""


def _print_rich_success(message: str):
    """Print success message using rich formatting."""
    if USE_RICH and RICH_AVAILABLE:
        console.print(
            Panel(
                Text(message, style="bold green"),
                title="Success",
                border_style="green",
                box=box.ROUNDED,
            )
        )
    else:
        print(message)


def _print_rich_error(title: str, *messages: str):
    """Print error messages using rich formatting."""
    if USE_RICH and RICH_AVAILABLE:
        content = Text()
        for i, msg in enumerate(messages):
            if i > 0:
                content.append("\n")
            content.append(msg, style="bold red" if i == 0 else "red")

        console.print(
            Panel(content, title="Error", border_style="red", box=box.ROUNDED)
        )
    else:
        print(f"{title}")
        for msg in messages:
            print(f"   {msg}")


def _print_rich_warning(title: str, *messages: str):
    """Print warning messages using rich formatting."""
    if USE_RICH and RICH_AVAILABLE:
        content = Text()
        for i, msg in enumerate(messages):
            if i > 0:
                content.append("\n")
            content.append(msg, style="bold yellow" if i == 0 else "yellow")

        console.print(
            Panel(content, title=" Warning", border_style="yellow", box=box.ROUNDED)
        )
    else:
        print(f"{title}")
        for msg in messages:
            print(f"   {msg}")


def _print_rich_diff(diff_output: str, file1: str, file2: str):
    """Print diff output using rich formatting."""
    if USE_RICH and RICH_AVAILABLE:
        # Create a table for file comparison
        table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
        table.add_column("File 1", style="cyan")
        table.add_column("File 2", style="magenta")

        def hard_wrap_filename(fname):
            width = int(console.width * 0.48)
            fname = str(fname)
            return "\n".join(fname[i : i + width] for i in range(0, len(fname), width))

        file1, file2 = hard_wrap_filename(file1), hard_wrap_filename(file2)
        table.add_row(file1, file2)
        console.print(Panel(table, title="Files Being Compared", border_style="yellow"))

        # Display diff output with syntax highlighting
        if diff_output.strip():
            syntax = Syntax(
                diff_output,
                "diff",
                theme="monokai",
                line_numbers=False,
                word_wrap=True,
            )
            console.print(
                Panel(
                    syntax,
                    title="Differences Found",
                    border_style="yellow",
                    box=box.ROUNDED,
                )
            )
    else:
        msgs = []
        msgs.append("DIFFERENCES FOUND:")
        msgs.append(f"File 1: {file1}")
        msgs.append(f"File 2: {file2}")
        msgs.append(diff_output)
        log_with_emphasis(LOG.error, msgs)


def _prompt_user_for_overwrite(file1: str, file2: str) -> bool:
    """Prompt user to confirm overwriting file1 with file2."""
    if USE_RICH and RICH_AVAILABLE:
        # Rich formatted prompt
        console.print(
            Panel(
                Text(
                    f"Do you want to overwrite:\n",
                    style="bold yellow",
                )
                + Text(
                    f"{file1}\n",
                    style="cyan",
                )
                + Text(
                    "with\n",
                    style="yellow",
                )
                + Text(
                    f"{file2}",
                    style="magenta",
                ),
                title="⚠️ Overwrite?",
                border_style="red",
                box=box.ROUNDED,
            )
        )
        response = console.input(
            "[bold red]Enter 'yes' or 'y' to confirm overwrite "
            "(or anything else to cancel): [/bold red]"
        )
    else:
        # Plain text prompt
        print(f"\n⚠️ Overwrite Confirmation")
        print(f"Do you want to overwrite:")
        print(f"  {file1}")
        print(f"with:")
        print(f"  {file2}?")
        response = input(
            "Enter 'yes' or 'y' to confirm overwrite (or anything else to cancel): "
        )

    return response.lower().strip() in ["yes", "y"]


def _handle_overwrite_prompt(file1: str, file2: str) -> bool:
    """Handle the overwrite prompt workflow."""
    if not PROMPT_TO_OVERWRITE_COMPARISON_FILE:
        return False

    if _prompt_user_for_overwrite(file1, file2):
        # Overwrite file1 with file2
        copy(file2, file1)

        success_msg = f"File overwritten successfully! {file2} has replaced {file1}."
        if USE_RICH and RICH_AVAILABLE:
            console.print(
                Panel(
                    Text(success_msg, style="bold green"),
                    title="Overwrite Complete",
                    border_style="green",
                    box=box.ROUNDED,
                )
            )
        else:
            print(f"{success_msg}")

        LOG.warning(f"Overwritten {file1} with {file2}")
        return True
    else:
        return False


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
            matches=(result.returncode == 0), diff_output=result.stdout
        )
    except Exception as e:
        LOG.error(f"Diff operation failed: {e}")
        raise


def log_comparison_result(result, output_product, compare_product, diff_file=None):
    """Log comparison results with optional console output."""
    if result.matches:
        log_with_emphasis(LOG.info, "GOOD Text files match")
        if PRINT_TO_CONSOLE:
            _print_rich_success("Text files match!")
        return

    log_messages = [
        "BAD Text files do NOT match exactly",
        f"output_product: {output_product}",
        f"compare_product: {compare_product}",
    ]
    if diff_file:
        log_messages.append(f"out_difftxt: {diff_file}")

    log_with_emphasis(LOG.interactive, *log_messages)

    if PRINT_TO_CONSOLE and result.diff_output:
        _print_rich_diff(result.diff_output, output_product, compare_product)

    # Handle overwrite prompt if files don't match


def write_diff_file(file1, file2, output_file):
    """Write diff output to a file."""
    with Path(output_file).open("w", encoding="utf-8") as fobj:
        subprocess.call(["diff", str(file1), str(file2)], stdout=fobj, timeout=30)


def outputs_match(plugin, output_product, compare_product):
    """Compare two text files for exact content match."""
    if not (
        correct_file_format(output_product) and correct_file_format(compare_product)
    ):
        raise ValueError("Both files must be valid text files")

    result = run_diff(output_product, compare_product)
    LOG.debug(result.diff_output)

    diff_file = None
    if not result.matches:
        diff_file = plugin.get_out_diff_fname(compare_product, output_product)
        write_diff_file(output_product, compare_product, diff_file)

    log_comparison_result(result, output_product, compare_product, diff_file)
    if not result.matches:
        if _handle_overwrite_prompt(compare_product, output_product):
            result.matches = True

    return result.matches


def call(plugin, compare_path, output_products):
    """Execute comparison workflow for output validation."""
    return plugin.compare_outputs(compare_path, output_products)


# =============================================================================
# TESTING UTILITIES
# =============================================================================

predictable_random = get_numpy_seeded_random_generator()


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
