"""Verify script-mode data extraction, manipulation, and reinsertion."""

from __future__ import annotations

import glob
import os

from geoips.interfaces import readers
from geoips.scripting import (
    RetentionPolicy,
    add_data_step,
    get_current_data,
    initialize_script_tree,
)


def main():
    """Read two ABI channels, compute a difference, and reinsert the result."""
    fnames = sorted(
        glob.glob(
            os.path.join(
                os.environ["GEOIPS_TESTDATA_DIR"],
                "test_data_abi/data/goes16_20200918_1950/*",
            )
        )
    )
    print("=== ABI reader manipulation script-mode verification ===")
    print(f"input_file_count={len(fnames)}")
    print(f"first_input_file={fnames[0] if fnames else None}")

    tree = initialize_script_tree(
        "reader_manipulation_verify",
        retention_policy=RetentionPolicy.keep_all,
    )
    reader = readers.get_plugin("abi_netcdf")

    tree = reader(
        data=tree,
        filenames=fnames,
        step_id="read_b14_b15",
        variables=["B14BT", "B15BT"],
    )

    current = get_current_data(tree)
    difference = current["B14BT"] - current["B15BT"]
    difference.name = "B14BT_minus_B15BT"
    difference.attrs["long_name"] = "ABI B14BT minus B15BT"
    difference.attrs["units"] = current["B14BT"].attrs.get("units", "")

    modified = current.copy()
    modified["B14BT_minus_B15BT"] = difference

    tree = add_data_step(
        tree,
        modified,
        step_id="calculate_b14_b15_difference",
    )

    current = get_current_data(tree)
    print(f"children={list(tree.children)}")
    print(f"current_data_vars={list(current.data_vars)}")
    print(f"current_dims={dict(current.sizes)}")
    print(
        "difference_range="
        f"({float(current['B14BT_minus_B15BT'].min()):.3f}, "
        f"{float(current['B14BT_minus_B15BT'].max()):.3f})"
    )

    assert "read_b14_b15" in tree.children
    assert "calculate_b14_b15_difference" in tree.children
    assert "B14BT_minus_B15BT" in current.data_vars
    assert tree["calculate_b14_b15_difference"].attrs["plugin_kind"] == "manual"


if __name__ == "__main__":
    main()
