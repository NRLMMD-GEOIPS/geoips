# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Pytest file for calling integration bash scripts."""

import os
import shlex
from datetime import datetime, timezone
import re

import pytest

from geoips.geoips_utils import call_cmd
from geoips.filenames.base_paths import PATHS as gpaths

print("")
for test_envvarname in [
    "GEOIPS_TEST_OUTPUT_CHECKER_THRESHOLD_IMAGE",
    "GEOIPS_TEST_PRINT_TEXT_OUTPUT_CHECKER_TO_CONSOLE",
    "GEOIPS_TEST_SUPPRESS_PYTEST_FAILED_LOG_CONTENTS",
    "GEOIPS_TEST_SECTOR_CREATE_ANNOTATED_OUTPUTS",
    "GEOIPS_TEST_SECTOR_CREATE_GEOTIFF_OUTPUTS",
    "GEOIPS_TEST_PROMPT_TO_OVERWRITE_COMPARISON_FILE_IF_MISMATCH",
]:
    print(f"{test_envvarname:>60s}: {gpaths[test_envvarname]}")

# ---------------------------------------------------------------------------
# Paths used by the ansible install checks
# ---------------------------------------------------------------------------
_REPO_ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", ".."))
_ANSIBLE_DIR = os.path.join(_REPO_ROOT, "tests", "ansible")
_PLAYBOOK = os.path.join(_ANSIBLE_DIR, "playbooks", "install.yml")
_INVENTORY = os.path.join(_ANSIBLE_DIR, "inventory", "local.yml")

# Quick test to ensure basic functionality in geoips installation.
# This test list should NOT require/test anything in any other plugin package.
base_integ_test_calls = [
    "$geoips_repopath/tests/scripts/amsr2.config_based_no_compare.sh",
    "$geoips_repopath/tests/scripts/amsr2_ocean.tc.windspeed.imagery_clean.sh",
]

# Linting integration tests, ensure code and documentation are correctly formatted.
lint_integ_test_calls = [
    "$geoips_repopath/tests/utils/check_code.sh all $repopath",
    "$geoips_repopath/docs/build_docs.sh $repopath $pkgname html_only",
]

# Test scripts validating plugins and interfaces.
# NOTE --package_name doesn't actually do anything yet for test_interfaces.py
validation_integ_test_calls = [
    "python $geoips_repopath/tests/utils/test_interfaces.py --package_name $pkgname --repo_path $repopath",  # noqa: E501
    "$geoips_repopath/tests/scripts/console_script_list_available_plugins.sh $pkgname $repopath",  # noqa: E501
]

# This includes ALL test scripts within the geoips repo itself with available data,
# excluding the tests under base and lint markers.
# This test list should NOT require/test anything in any other plugin package.
full_integ_test_calls = [
    "$geoips_repopath/tests/scripts/abi.config_based_output_low_memory_resource_usage_logging.sh",  # noqa: E501
    "$geoips_repopath/tests/scripts/abi.static.Infrared.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/abi.static.Infrared.imagery_annotated_enhanced.sh",
    "$geoips_repopath/tests/scripts/console_script_create_sector_image.sh",
    "$geoips_repopath/tests/scripts/abi.static.dmw.imagery_windbarbs_high.sh",
    "$geoips_repopath/tests/scripts/abi.static.Test-Visible-Logarithmic.imagery_clean.sh",  # noqa: E501
    "$geoips_repopath/tests/scripts/abi.static.Visible.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/abi.static.nasa_dust_rgb.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/abi.config_based_dmw_overlay.sh",
    "$geoips_repopath/tests/scripts/abi.config_based_output_full_zarr_cache_backend.sh",
    "$geoips_repopath/tests/scripts/abi.config_based_output_low_memory.sh",
    "$geoips_repopath/tests/scripts/abi.config_based_output.sh",
    "$geoips_repopath/tests/scripts/ami.static.Infrared.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/ami.static.Visible.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/ami.static.mst.absdiff-IR-BD.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/ami.tc.WV.geotiff.sh",
    "$geoips_repopath/tests/scripts/ami.WV-Upper.unprojected_image.sh",
    "$geoips_repopath/tests/scripts/amsr2.global.89H-Physical.cogeotiff.sh",
    "$geoips_repopath/tests/scripts/amsr2.tc.89H-Physical.imagery_annotated.sh",
    "$geoips_repopath/tests/scripts/amsr2.tc.89H-Physical.imagery_annotated_colorhist.sh",  # noqa: E501
    "$geoips_repopath/tests/scripts/amsr2_rss.tc.windspeed.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/amsr2.config_based_overlay_output.sh",
    "$geoips_repopath/tests/scripts/amsr2.config_based_overlay_output_low_memory.sh",
    "$geoips_repopath/tests/scripts/amsua_mhs_mirs.tc.rainrate.imagery.sh",
    "$geoips_repopath/tests/scripts/ascat_knmi.tc.windbarbs.imagery_windbarbs_clean.sh",
    "$geoips_repopath/tests/scripts/ascat_low_knmi.tc.windbarbs.imagery_windbarbs.sh",
    "$geoips_repopath/tests/scripts/ascat_noaa_25km.tc.windbarbs.imagery_windbarbs.sh",
    "$geoips_repopath/tests/scripts/ascat_noaa_50km.tc.wind-ambiguities.imagery_windbarbs.sh",  # noqa: E501
    "$geoips_repopath/tests/scripts/ascat_uhr.tc.wind-ambiguities.imagery_windbarbs.sh",
    "$geoips_repopath/tests/scripts/ascat_uhr.tc.nrcs.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/ascat_uhr.tc.windbarbs.imagery_windbarbs.sh",
    "$geoips_repopath/tests/scripts/ascat_uhr.tc.windspeed.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/atms.tc.165H.netcdf_geoips.sh",
    "$geoips_repopath/tests/scripts/aws_TB50.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/aws_TB89.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/aws_TB165.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/aws_TB180.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/aws_TB325-1.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/aws_tc_TB50.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/aws_tc_TB89.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/aws_tc_TB165.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/aws_tc_TB180.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/aws_tc_TB325-1.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/cli_dummy_script.sh",
    "$geoips_repopath/tests/scripts/fci.static.Visible.imagery_annotated.sh",
    "$geoips_repopath/tests/scripts/fci.unprojected_image.Infrared.sh",
    "$geoips_repopath/tests/scripts/gfs.static.windspeed.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/gfs.static.waveheight.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/gmi.tc.89pct.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/imerg.tc.Rain.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/mhs_mirs.tc.183-3H.imagery_annotated.sh",
    "$geoips_repopath/tests/scripts/mimic_coarse.static.TPW-CIMSS.imagery_annotated.sh",
    "$geoips_repopath/tests/scripts/mimic_fine.tc.TPW-PWAT.imagery_annotated.sh",
    "$geoips_repopath/tests/scripts/modis.Infrared.unprojected_image.sh",
    "$geoips_repopath/tests/scripts/oscat_knmi.tc.windbarbs.imagery_windbarbs.sh",
    "$geoips_repopath/tests/scripts/sar.tc.nrcs.imagery_annotated.sh",
    "$geoips_repopath/tests/scripts/seviri.WV-Upper.unprojected_image.sh",
    "$geoips_repopath/tests/scripts/seviri.airmass.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/seviri.Convective_Storms.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/seviri.Day_Microphys_Summer.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/seviri.Day_Microphys_Winter.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/seviri.Day_Solar.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/seviri.Dust_RGB.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/seviri.Natural_Color.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/seviri.Night_Microphys.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/seviri.Volcanic_Ash.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/sgli.static.IR-RGB.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/smap.unsectored.text_winds.sh",
    "$geoips_repopath/tests/scripts/smos.tc.sectored.text_winds.sh",
    "$geoips_repopath/tests/scripts/viirs.static.visible.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/viirsday.global.Night-Vis-IR.cogeotiff_rgba.sh",
    "$geoips_repopath/tests/scripts/viirsday.tc.Night-Vis-IR.imagery_annotated.sh",
    "$geoips_repopath/tests/scripts/viirsmoon.tc.Night-Vis-GeoIPS1.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/seviri.WV-Upper.no_self_register.unprojected_image.sh",  # noqa: E501
    "$geoips_repopath/tests/scripts/viirsclearnight.Night-Vis-IR-GeoIPS1.unprojected_image.sh",  # noqa: E501
]

# Test scripts spanning multiple repositories / geoips plugins.
multi_repo_integ_test_calls = [
    "python $GEOIPS_PACKAGES_DIR/geoips/tests/utils/test_interfaces.py",
    "$geoips_repopath/tests/scripts/console_script_list_available_plugins.sh",
]

# Test scripts that require test datasets with limited availability.
limited_data_integ_test_calls = [
    "$geoips_repopath/tests/scripts/ewsg.static.Infrared.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/hy2.tc.windspeed.imagery_annotated.sh",
    "$geoips_repopath/tests/scripts/saphir.tc.183-3HNearest.imagery_annotated.sh",
    "$geoips_repopath/tests/scripts/ssmi.tc.37pct.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/ssmis.color91.unprojected_image.sh",
]


def set_log_filename(expanded_call):
    """Set the log filename for individual pytest outputs."""
    script_name = expanded_call[0]
    # Strip out any full paths, if a test has a full path passed in
    # Also replace any "*" with "-"
    args_str = ""
    for curr_arg in expanded_call[1:]:
        if "/" in curr_arg:
            curr_arg = os.path.basename(curr_arg)
        args_str = f"{args_str}_{curr_arg}".replace("*", "-")
    curr_datetime = datetime.utcnow().strftime("%Y%m%d.%H%M%S")
    basename_str = os.path.basename(script_name)
    log_fname = f"{os.environ['GEOIPS_OUTDIRS']}/logs/pytests/integration"
    log_fname = f"{log_fname}/{curr_datetime}.{basename_str}{args_str}.log"
    return log_fname


# ---------------------------------------------------------------------------
# Ansible-based install verification
# ---------------------------------------------------------------------------

def _run_ansible_check(tags, label):
    """Run the ansible install playbook for the given tier tags.

    The playbook is idempotent — if everything is already installed the tasks
    are no-ops.  If something is missing ansible will attempt to install it;
    if that also fails the non-zero exit code propagates as a RuntimeError.

    Registries are skipped because the tests themselves may need to recreate
    them after mounting additional plugins.

    Parameters
    ----------
    tags : str
        Comma-separated ansible tags, e.g. ``"base"`` or ``"base,full"``.
    label : str
        Human-readable label for log file naming.

    Raises
    ------
    RuntimeError
        If the ansible playbook exits non-zero.
    """
    cmd = [
        "ansible-playbook",
        _PLAYBOOK,
        "-i", _INVENTORY,
        "--tags", tags,
        "--skip-tags", "registries",
        "-v",
    ]

    log_fname = set_log_filename(["ansible-check", label])
    print(f"Ansible install check ({label}), log: {log_fname}")

    # Point ansible at our config and roles directory.
    # ANSIBLE_CONFIG finds the config file.
    # ANSIBLE_ROLES_PATH provides an absolute path to roles/ so they resolve
    # regardless of the working directory (roles_path in ansible.cfg is
    # relative to CWD, which varies under pytest).
    env_override = {
        "ANSIBLE_CONFIG": os.path.join(_ANSIBLE_DIR, "ansible.cfg"),
        "ANSIBLE_ROLES_PATH": os.path.join(_ANSIBLE_DIR, "roles"),
    }
    orig_vals = {}
    for key, val in env_override.items():
        orig_vals[key] = os.environ.get(key)
        os.environ[key] = val

    try:
        retval, stdout, stderr = call_cmd(
            cmd, output_log_fname=log_fname, use_logging=False, use_print=False
        )
    finally:
        # Restore original env
        for key, orig in orig_vals.items():
            if orig is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = orig

    if retval != 0:
        print(f"\nAnsible install check '{label}' failed, exiting")
        print(f"Log: {log_fname}")
        raise RuntimeError(
            f"Ansible install check '{label}' failed, "
            f"see error output in log {log_fname}\n"
        )


def check_base_install():
    """Verify the base GeoIPS installation via ansible.

    Runs the install playbook with ``--tags base`` (registries skipped).
    Because ansible is idempotent, already-installed components are fast
    no-ops; anything missing is installed or the check fails.
    """
    _run_ansible_check("base", "base_install")


def check_full_install():
    """Verify the full GeoIPS installation via ansible.

    Runs the install playbook with ``--tags base,full`` (registries skipped).
    """
    _run_ansible_check("base,full", "full_install")


def check_site_install():
    """Verify the site GeoIPS installation via ansible.

    Runs the install playbook with ``--tags base,full,site``
    (registries skipped).
    """
    _run_ansible_check("base,full,site", "site_install")


def check_environment(check_environment_script):
    """Call check environment script to confirm environment is set appropriately."""
    print("Checking environment")
    cmd = ["bash", check_environment_script]
    log_fname = set_log_filename([os.path.basename(check_environment_script)])
    print(f"Check environment log: {log_fname}")
    retval, stdout, stderr = call_cmd(
        cmd, output_log_fname=log_fname, use_logging=False, use_print=False
    )
    if retval != 0:
        print(f"\nCall to '{check_environment_script}' failed, exiting")
        print("See error output in log:")
        print(f"Log: {log_fname}")
        raise RuntimeError(
            f"Check environment failed, please see error output in log {log_fname}\n"
        )


def setup_environment():
    """Set up necessary environment variables for integration tests.

    Configures paths and package names for the GeoIPS core and its plugins by
    setting environment variables required for the integration tests.  Assumes
    that ``GEOIPS_PACKAGES_DIR`` is already set in the environment.

    Notes
    -----
    The following environment variables are set:

    - geoips_repopath
    - geoips_pkgname
    """
    os.environ["geoips_repopath"] = _REPO_ROOT
    os.environ["geoips_pkgname"] = "geoips"

    geoips_packages_dir = os.getenv("GEOIPS_PACKAGES_DIR")
    if not geoips_packages_dir:
        raise EnvironmentError("GEOIPS_PACKAGES_DIR environment variable not set.")


@pytest.fixture(scope="session")
def site_setup():
    """Set up the site integration tests by checking install and setting env-vars."""
    check_site_install()


@pytest.fixture(scope="session")
def base_setup():
    """Set up the base integration tests by checking install and setting env-vars."""
    check_base_install()


@pytest.fixture(scope="session")
def full_setup():
    """Set up the full integration tests by checking install and setting env-vars."""
    check_full_install()


def is_likely_oserror_missing_file(log_contents: str) -> bool:
    """Check if the log contents indicate a likely OSError for a missing file.

    Searches the last ten lines of the provided log contents for patterns
    that suggest an OSError related to a missing file.

    Parameters
    ----------
    log_contents : str
        The contents of the log file to check.

    Returns
    -------
    bool
        True if the log contents indicate a likely OSError for a missing file,
        False otherwise.
    """
    last_ten_lines = "\n".join(log_contents.strip().splitlines()[-10:])
    pattern = r"OSError: (File '[^']+' not found|No files found on disk)\."
    return re.search(pattern, last_ten_lines) is not None


def run_script_with_bash(script, fail_on_missing_data, unset_output_path_env_vars=True):
    """Run scripts by executing specified shell commands with bash.

    If unset_output_path_env_vars is set, explicit output path env vars are
    unset to ensure clean consistent paths for test comparisons (these env
    vars all default to a consistent location if not set, so ensure they are
    not set so output products are written to a consistent location for tests).

    Parameters
    ----------
    script : str
        Shell command to execute.  The command may contain environment
        variables which will be expanded before execution.
    fail_on_missing_data : bool
        If True, raise FileNotFoundError when data is missing.
        If False, xfail the test instead.
    unset_output_path_env_vars : bool, optional
        If True, unset output path env vars for test consistency.

    Raises
    ------
    subprocess.CalledProcessError
        If the shell command returns a non-zero exit status.
    """
    print("")
    removed_env_vars = {}
    if unset_output_path_env_vars:
        for env_var in gpaths["GEOIPS_REPLACE_OUTPUT_PATHS"]:
            if env_var in os.environ:
                removed_env_vars[env_var] = os.environ[env_var]
                del os.environ[env_var]
        if removed_env_vars:
            print(f"REMOVED ENV VARS {removed_env_vars.keys()}")
    else:
        print("NOT REMOVING ENV VARS!")

    if fail_on_missing_data:
        print("FAILING ON MISSING DATA!")
    else:
        print("NOT FAILING ON MISSING DATA!")

    if not gpaths["GEOIPS_TEST_SUPPRESS_PYTEST_FAILED_LOG_CONTENTS"]:
        print("DUMPING ALL BAD LOG CONTENTS TO TERMINAL!")
    else:
        print("SUPPRESSING BAD LOG CONTENTS TO TERMINAL!")

    if ".sh" in script:
        expanded_call = shlex.split("bash " + os.path.expandvars(script))
    else:
        expanded_call = shlex.split(os.path.expandvars(script))
    log_fname = set_log_filename(expanded_call[1:])

    print(f"Log: {log_fname} , latest logs:")
    print(f"ls -lthr {os.path.dirname(log_fname)}/*")
    print(datetime.now(timezone.utc))
    retval, stdout, stderr = call_cmd(
        expanded_call,
        output_log_fname=log_fname,
        use_logging=False,
        use_print=False,
        pipe=True,
    )
    if removed_env_vars:
        print(f"RESTORING ENV VARS {removed_env_vars.keys()}")
        for env_var in removed_env_vars:
            os.environ[env_var] = removed_env_vars[env_var]
    if retval != 0:
        with open(log_fname, "r") as logfile:
            log_contents = logfile.read()
            if not gpaths["GEOIPS_TEST_SUPPRESS_PYTEST_FAILED_LOG_CONTENTS"]:
                print("\nLOG FILE CONTENTS:\n")
                print(log_contents)
                print("-" * 80)
        print("FAILED COMMAND FOR PREVIOUS TEST")
        print(" ".join(expanded_call))
        print(f"FAILED LOG FILE: {log_fname}")
        print("FAILED")

        if is_likely_oserror_missing_file(log_contents):
            if fail_on_missing_data:
                raise FileNotFoundError(
                    f"FileNotFoundError, see output in log {log_fname}\n"
                )
            else:
                pytest.xfail(f"FileNotFoundError, see output in log {log_fname}\n")
        else:
            raise RuntimeError(f"CalledProcessError, see output in log {log_fname}\n")
    else:
        print("PASSED COMMAND FOR PREVIOUS TEST")
        print(" ".join(expanded_call))
        print(f"PASSED LOG FILE: {log_fname}")
        print("PASSED")


@pytest.mark.base
@pytest.mark.integration
@pytest.mark.parametrize("script", base_integ_test_calls)
def test_integ_base_test_script(
    base_setup: None, script: str, fail_on_missing_data: bool
):
    """Run base integration test scripts.

    Parameters
    ----------
    script : str
        Shell command to execute as part of the integration test.
    fail_on_missing_data : bool
        Whether to hard-fail on missing test data.

    Raises
    ------
    subprocess.CalledProcessError
        If the shell command returns a non-zero exit status.
    """
    setup_environment()
    run_script_with_bash(script, fail_on_missing_data=fail_on_missing_data)


@pytest.mark.lint
@pytest.mark.integration
@pytest.mark.parametrize("script", lint_integ_test_calls)
def test_integ_lint_test_script(base_setup: None, script: str):
    """Run lint integration test scripts.

    Parameters
    ----------
    script : str
        Shell command to execute as part of the integration test.

    Raises
    ------
    subprocess.CalledProcessError
        If the shell command returns a non-zero exit status.
    """
    setup_environment()
    run_script_with_bash(script)


@pytest.mark.validation
@pytest.mark.integration
@pytest.mark.parametrize("script", validation_integ_test_calls)
def test_integ_validation_script(base_setup: None, script: str):
    """
    Run integration test scripts by executing specified shell commands.

    Parameters
    ----------
    script : str
        Shell command to execute as part of the integration test. The command may
        contain environment variables which will be expanded before execution.

    Raises
    ------
    subprocess.CalledProcessError
        If the shell command returns a non-zero exit status.
    """
    setup_environment()
    run_script_with_bash(script)


@pytest.mark.full
@pytest.mark.spans_multiple_packages
@pytest.mark.integration
@pytest.mark.parametrize("script", multi_repo_integ_test_calls)
def test_integ_multi_repo_script(
    site_setup: None, script: str, fail_on_missing_data: bool
):
    """Run multi-repo integration test scripts.

    Parameters
    ----------
    script : str
        Shell command to execute as part of the integration test.
    fail_on_missing_data : bool
        Whether to hard-fail on missing test data.

    Raises
    ------
    subprocess.CalledProcessError
        If the shell command returns a non-zero exit status.
    """
    setup_environment()
    run_script_with_bash(script, fail_on_missing_data=fail_on_missing_data)


@pytest.mark.full
@pytest.mark.integration
@pytest.mark.parametrize("script", full_integ_test_calls)
def test_integ_full_script(full_setup: None, script: str, fail_on_missing_data: bool):
    """Run full integration test scripts.

    Parameters
    ----------
    script : str
        Shell command to execute as part of the integration test.
    fail_on_missing_data : bool
        Whether to hard-fail on missing test data.

    Raises
    ------
    subprocess.CalledProcessError
        If the shell command returns a non-zero exit status.
    """
    setup_environment()
    run_script_with_bash(script, fail_on_missing_data=fail_on_missing_data)


# These are required to test the full functionality of this repo, but have limited
# test dataset availability.
@pytest.mark.full
@pytest.mark.optional
@pytest.mark.integration
@pytest.mark.parametrize("script", limited_data_integ_test_calls)
def test_integ_limited_data_script(
    full_setup: None, script: str, fail_on_missing_data: bool
):
    """Run limited-data integration test scripts.

    Parameters
    ----------
    script : str
        Shell command to execute as part of the integration test.
    fail_on_missing_data : bool
        Whether to hard-fail on missing test data.

    Raises
    ------
    subprocess.CalledProcessError
        If the shell command returns a non-zero exit status.
    """
    setup_environment()
    run_script_with_bash(script, fail_on_missing_data=fail_on_missing_data)
