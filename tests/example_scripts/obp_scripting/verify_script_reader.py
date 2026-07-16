"""Scratch verification for script-mode reader invocation."""

from __future__ import annotations

import glob
import os

from geoips.interfaces import readers
from geoips.scripting import RetentionPolicy, get_current_data, initialize_script_tree


def main():
    """Call a real reader using an initialized script tree."""
    fnames = sorted(
        glob.glob(
            os.path.join(
                os.environ["GEOIPS_TESTDATA_DIR"],
                "test_data_abi/data/goes16_20200918_1950/*",
            )
        )
    )
    print(f"input_file_count={len(fnames)}")

    tree = initialize_script_tree(
        "reader_verify",
        retention_policy=RetentionPolicy.keep_all,
    )
    reader = readers.get_plugin("abi_netcdf")

    tree = reader(
        data=tree,
        filenames=fnames,
        step_id="read_b14_b15",
        variables=["B14BT", "B15BT"],
    )

    print(f"children={list(tree.children)}")
    print(f"reader_attrs={dict(tree['read_b14_b15'].attrs)}")

    current = get_current_data(tree)
    print(f"current_data_vars={list(current.data_vars)}")
    print(f"current_coords={list(current.coords)}")
    print(f"current_dims={dict(current.sizes)}")

    assert "read_b14_b15" in tree.children
    assert tree["read_b14_b15"].attrs["plugin_kind"] == "reader"
    assert "B14BT" in current.data_vars
    assert "B15BT" in current.data_vars


if __name__ == "__main__":
    main()
