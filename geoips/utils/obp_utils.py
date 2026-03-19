# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Utility functions for the order-based procflow."""

import os


def validate_workflow_file_inputs(workflow_plugin, fnames):
    """Validate that all required file inputs exist before processing begins.

    Checks that file paths required by workflow steps are accessible on the
    filesystem. Inspects command-line `fnames`, per-step `fnames` lists,
    and `compare_path` values. If any paths are missing the workflow is
    terminated with an actionable error message.

    Parameters
    ----------
    workflow_plugin : dict
        The raw workflow plugin dictionary whose `spec.steps` will be
        inspected.
    fnames : list of str
        List of input filenames provided on the command line for reader steps.

    Raises
    ------
    FileNotFoundError
        If one or more required file paths do not exist.
    """
    missing = []

    for path in fnames:
        if not os.path.exists(path):
            missing.append(("command_line_args", "reader", path))

    for step_id, step_def in workflow_plugin["spec"]["steps"].items():
        kind = step_def["kind"]
        arguments = step_def.get("arguments", {})

        for path in arguments.get("fnames", []):
            if not os.path.exists(path):
                missing.append((step_id, kind, path))

        compare_path = arguments.get("compare_path", None)
        if compare_path and not os.path.exists(compare_path):
            missing.append((step_id, kind, compare_path))

    if missing:
        error_lines = [
            "The workflow cannot proceed because the following required "
            "file(s) were not found:"
        ]
        for step_id, kind, path in missing:
            error_lines.append(f"  step '{step_id}' (kind: {kind}): {path}")

        raise FileNotFoundError("\n".join(error_lines))
