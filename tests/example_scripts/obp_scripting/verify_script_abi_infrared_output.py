"""Verify an ABI infrared scripted OBP-style plugin sequence."""

from __future__ import annotations

import argparse
import glob
import os
from pathlib import Path

from geoips.interfaces import (
    algorithms,
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
    attach_plugin_result,
    get_current_data,
    get_output_products,
    initialize_script_tree,
)


INTERESTING_ATTRS = (
    "plugin_kind",
    "plugin_name",
    "step_id",
    "retention_policy",
    "source_name",
    "platform_name",
    "product_name",
    "area_id",
    "coverage",
    "output_filenames",
    "output_products",
)


def _short_value(value, max_len=120):
    """Return a compact representation for diagnostic printing."""
    text = repr(value)
    if len(text) > max_len:
        return f"{text[: max_len - 3]}..."
    return text


def _summarize_dataset(dataset):
    """Return a small summary of an xarray Dataset-like object."""
    if dataset is None:
        return {"dataset": None}
    return {
        "dims": dict(dataset.sizes),
        "data_vars": list(dataset.data_vars),
        "coords": list(dataset.coords),
    }


def _summarize_attrs(attrs):
    """Return selected attrs useful for following script execution."""
    return {
        key: _short_value(attrs[key])
        for key in INTERESTING_ATTRS
        if key in attrs
    }


def _print_step(tree, step_id):
    """Print a compact diagnostic summary for one script step."""
    node = tree[step_id]
    print(f"  step={step_id!r}")
    print(f"    attrs={_summarize_attrs(node.attrs)}")
    print(f"    dataset={_summarize_dataset(node.ds)}")
    if node.children:
        print(f"    children={list(node.children)}")
        for child_name, child in node.children.items():
            print(f"      child={child_name!r} {_summarize_dataset(child.ds)}")


def _print_checkpoint(tree, label, step_id=None):
    """Print script-tree state after a step completes."""
    print(f"\n--- {label} ---")
    print(f"tree_children={list(tree.children)}")
    if step_id is not None:
        _print_step(tree, step_id)
    try:
        current = get_current_data(tree)
    except ValueError as exc:
        print(f"current_data=unavailable ({exc})")
    else:
        print(f"current_data={_summarize_dataset(current)}")


def _parse_args():
    """Parse command line arguments for the verification script."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--retention-policy",
        choices=[policy.value for policy in RetentionPolicy],
        default=RetentionPolicy.keep_all.value,
        help="Script DataTree retention policy to use.",
    )
    return parser.parse_args()


def main():
    """Run ABI infrared processing from reader through output formatter."""
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
    print("=== ABI infrared script-mode verification ===")
    print(f"input_file_count={len(fnames)}")
    print(f"first_input_file={fnames[0] if fnames else None}")
    print("GEOIPS_OUTDIRS=" + repr(os.environ.get("GEOIPS_OUTDIRS")))
    print(f"retention_policy={retention_policy.value}")

    tree = initialize_script_tree(
        "abi_infrared_script_verify",
        retention_policy=retention_policy,
    )
    _print_checkpoint(tree, "initialized script tree")

    tree = readers.get_plugin("abi_netcdf")(
        data=tree,
        filenames=fnames,
        step_id="read_data",
        variables=["B14BT"],
    )
    _print_checkpoint(tree, "after reader", "read_data")

    sector = sectors.get_plugin("conus")()
    tree = attach_plugin_result(
        tree,
        sector,
        step_id="load_sector",
        plugin_kind="sector",
        plugin_name="conus",
    )
    _print_checkpoint(tree, "after sector", "load_sector")

    tree = interpolators.get_plugin("interp_nearest")(
        data=tree,
        step_id="interpolate_data",
        varlist=["B14BT"],
    )
    _print_checkpoint(tree, "after interpolator", "interpolate_data")

    tree = algorithms.get_plugin("single_channel")(
        data=tree,
        step_id="apply_algorithm",
        output_data_range=[-90.0, 30.0],
        input_units="Kelvin",
        output_units="celsius",
        min_outbounds="crop",
        max_outbounds="crop",
        norm=False,
        inverse=False,
    )
    _print_checkpoint(tree, "after algorithm", "apply_algorithm")

    tree = colormappers.get_plugin("Infrared")(
        data=tree,
        step_id="build_colormap",
        data_range=[-90.0, 30.0],
    )
    _print_checkpoint(tree, "after colormapper", "build_colormap")

    tree = coverage_checkers.get_plugin("masked_arrays")(
        data=tree,
        step_id="check_coverage",
        variable_name="data",
    )
    _print_checkpoint(tree, "after coverage checker", "check_coverage")

    tree = filename_formatters.get_plugin("geoips_fname")(
        data=tree,
        step_id="format_filename",
        product_name="Infrared",
        output_type="png",
    )
    _print_checkpoint(tree, "after filename formatter", "format_filename")

    tree = output_formatters.get_plugin("imagery_clean")(
        data=tree,
        step_id="write_image",
        product_name="Infrared",
        product_name_title="G16 Infrared @ 11.2 um",
    )
    _print_checkpoint(tree, "after output formatter", "write_image")

    output_products = get_output_products(tree, step_id="write_image")
    print("\n=== Final output products ===")
    print(f"output_products={output_products}")

    assert output_products
    for output_product in output_products:
        output_path = Path(output_product)
        print(f"exists={output_path.exists()} path={output_path}")
        assert output_path.exists(), output_product


if __name__ == "__main__":
    main()
