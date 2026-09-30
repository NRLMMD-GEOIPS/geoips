"""Verify scripted plugin calls mixed with manual channel-difference code."""

from __future__ import annotations

import argparse
import glob
import os
from pathlib import Path

from geoips.interfaces import (
    colormappers,
    coverage_checkers,
    filename_formatters,
    interpolators,
    output_formatters,
    readers,
    sectors,
)
from geoips.scripting import (
    RetentionPolicy,
    add_data_step,
    attach_plugin_result,
    get_current_data,
    get_output_products,
    initialize_script_tree,
)

PRODUCT_NAME = "B14BT_minus_B15BT"


def _summarize_dataset(dataset):
    """Return compact dataset information for diagnostic output."""
    return {
        "dims": dict(dataset.sizes),
        "data_vars": list(dataset.data_vars),
        "coords": list(dataset.coords),
    }


def _print_checkpoint(tree, label):
    """Print a compact view of the current script tree state."""
    print(f"\n--- {label} ---")
    print(f"tree_children={list(tree.children)}")
    current = get_current_data(tree)
    print(f"current_data={_summarize_dataset(current)}")
    if PRODUCT_NAME in current:
        print(
            "difference_range="
            f"({float(current[PRODUCT_NAME].min()):.3f}, "
            f"{float(current[PRODUCT_NAME].max()):.3f})"
        )


def _parse_args():
    """Parse command line arguments for the verification script."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--retention-policy",
        choices=[policy.value for policy in RetentionPolicy],
        default=RetentionPolicy.metadata_only.value,
        help="Script DataTree retention policy to use.",
    )
    return parser.parse_args()


def main():
    """Read ABI channels, manually difference them, and write an image."""
    args = _parse_args()
    retention_policy = RetentionPolicy(args.retention_policy)
    fnames = sorted(
        glob.glob(
            os.path.join(
                os.environ["GEOIPS_TESTDATA_DIR"],
                "test_data_abi/data/goes16_20200918_1950/*",
            )
        )
    )

    print("=== ABI manual channel-difference script verification ===")
    print(f"input_file_count={len(fnames)}")
    print(f"retention_policy={retention_policy.value}")

    tree = initialize_script_tree(
        "abi_manual_difference_script_verify",
        retention_policy=retention_policy,
    )

    tree = readers.get_plugin("abi_netcdf")(
        data=tree,
        filenames=fnames,
        step_id="read_b14_b15",
        variables=["B14BT", "B15BT"],
    )
    _print_checkpoint(tree, "after reader")

    current = get_current_data(tree)
    difference = current["B14BT"] - current["B15BT"]
    difference.name = PRODUCT_NAME
    difference.attrs.update(
        {
            "long_name": "ABI B14BT minus B15BT brightness temperature",
            "units": current["B14BT"].attrs.get("units", "K"),
        }
    )
    manual = current[[]].copy(deep=True)
    manual[PRODUCT_NAME] = difference
    manual.attrs.update(current.attrs)

    tree = add_data_step(
        tree,
        manual,
        step_id="calculate_channel_difference",
    )
    _print_checkpoint(tree, "after manual channel difference")

    sector = sectors.get_plugin("conus")()
    tree = attach_plugin_result(
        tree,
        sector,
        step_id="load_sector",
        plugin_kind="sector",
        plugin_name="conus",
    )
    _print_checkpoint(tree, "after sector")

    tree = interpolators.get_plugin("interp_nearest")(
        data=tree,
        step_id="interpolate_difference",
        varlist=[PRODUCT_NAME],
    )
    _print_checkpoint(tree, "after interpolator")

    tree = colormappers.get_plugin("matplotlib_linear_norm")(
        data=tree,
        step_id="build_colormap",
        data_range=[-10.0, 10.0],
        cmap_name="RdBu_r",
        cbar_label="B14BT - B15BT (K)",
    )
    _print_checkpoint(tree, "after colormapper")

    tree = coverage_checkers.get_plugin("masked_arrays")(
        data=tree,
        step_id="check_coverage",
        variable_name=PRODUCT_NAME,
    )
    _print_checkpoint(tree, "after coverage checker")

    tree = filename_formatters.get_plugin("geoips_fname")(
        data=tree,
        step_id="format_filename",
        product_name=PRODUCT_NAME,
        output_type="png",
    )
    _print_checkpoint(tree, "after filename formatter")

    tree = output_formatters.get_plugin("imagery_clean")(
        data=tree,
        step_id="write_image",
        product_name=PRODUCT_NAME,
        product_name_title="ABI B14BT - B15BT",
    )
    _print_checkpoint(tree, "after output formatter")

    output_products = get_output_products(tree, step_id="write_image")
    print("\n=== Final output products ===")
    print(f"output_products={output_products}")
    for output_product in output_products:
        output_path = Path(output_product)
        print(f"exists={output_path.exists()} path={output_path}")
        assert output_path.exists(), output_product


if __name__ == "__main__":
    main()
