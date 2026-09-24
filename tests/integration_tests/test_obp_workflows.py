# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Integration tests for order-based procflow (OBP) workflow YAML plugins.

Each test loads a workflow plugin, checks that test data is available, and
runs the workflow end-to-end using ``geoips test wf <workflow_name>``.  Tests are
marked as expected failures (``xfail``) when the requied test data is unavailable.
"""

# Python Standard Libraries
from datetime import datetime, timezone
import os
from pathlib import Path
import shlex

# Third-party Libraries
import pytest

# GeoIPS Libraries
from geoips.geoips_utils import call_cmd
from geoips.interfaces import workflows

ami_workflow_names = [
    "ami_static_infrared_imagery_clean",
    "ami_static_visible_imagery_clean",
]

seviri_workflow_names = [
    "seviri_airmass_imagery_clean",
    "seviri_convective_storms_imagery_clean",
    "seviri_day_microphys_summer_imagery_clean",
    "seviri_day_microphys_winter_imagery_clean",
    "seviri_day_solar_imagery_clean",
    "seviri_dust_rgb_imagery_clean",
    "seviri_natural_color_imagery_clean",
    "seviri_night_microphys_imagery_clean",
    "seviri_volcanic_ash_imagery_clean",
    "seviri_wv_upper_no_self_register_unprojected_image",
]


def _run_obp_workflow(workflow_name, fail_on_missing_data):
    """Load a workflow plugin and run it using ``geoips test wf``.

    Parameters
    ----------
    workflow_name : str
        Registered workflow plugin name.
    fail_on_missing_data : bool
        If True, hard-fail when test data files are missing.
        If False, xfail instead.

    Raises
    ------
    FileNotFoundError
        If test data is missing and ``fail_on_missing_data`` is True.
    RuntimeError
        If the ``geoips test wf`` command exits non-zero.
    """
    workflow_plugin_object = workflows.get_plugin(workflow_name)
    filenames = workflow_plugin_object["test"]["filenames"]

    missing_filenames = [fname for fname in filenames if not Path(fname).exists()]
    if missing_filenames:
        msg = (
            f"OBP workflow '{workflow_name}' missing {len(missing_filenames)} of "
            f"{len(filenames)} test data files. First missing: {missing_filenames[0]}"
        )
        if fail_on_missing_data:
            raise FileNotFoundError(msg)
        pytest.xfail(msg)

    cmd = shlex.split(f"geoips test wf {workflow_name}")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d.%H%M%S")

    log_fname = (
        f"{os.environ['GEOIPS_OUTDIRS']}/logs/pytests/integration"
        f"/{timestamp}.{workflow_name}.log"
    )

    retval, stdout_list, stderr_list = call_cmd(
        cmd,
        output_log_fname=log_fname,
        use_logging=False,
        use_print=False,
        pipe=True,
    )

    if retval != 0:
        combined = ("".join(stdout_list) + "".join(stderr_list)).strip()
        summary = "\n".join(combined.splitlines()[-25:])
        raise RuntimeError(
            f"OBP workflow '{workflow_name}' failed (exit {retval}).\n"
            f"Log: {log_fname}\n{summary}"
        )


all_workflow_names = ami_workflow_names + seviri_workflow_names


@pytest.mark.full
@pytest.mark.integration
@pytest.mark.parametrize("workflow_name", all_workflow_names)
def test_obp_workflow(workflow_name, fail_on_missing_data):
    """Run OBP workflow end-to-end via ``geoips test wf``.

    Parameters
    ----------
    workflow_name : str
        Registered workflow plugin name.
    fail_on_missing_data : bool
        Whether to hard-fail when test data is unavailable.

    Raises
    ------
    FileNotFoundError
        If test data is missing and ``fail_on_missing_data`` is True.
    RuntimeError
        If the workflow exits non-zero.
    """
    _run_obp_workflow(workflow_name, fail_on_missing_data)
