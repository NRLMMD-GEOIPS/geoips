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

print(
    "\nOUTPUT_CHECKER_THRESHOLD_IMAGE: "
    f"{os.environ.get('OUTPUT_CHECKER_THRESHOLD_IMAGE')}\n"
)

# Quick test to ensure basic functionality in geoips installation.
# This test list should NOT require/test anything in any other plugin package.
base_integ_test_calls = [
    "$geoips_repopath/tests/scripts/amsr2.config_based_no_compare.sh",
    "$geoips_repopath/tests/scripts/amsr2_ocean.tc.windspeed.imagery_clean.sh",
]

# Linting integration tests, ensure code and documentation are correctly formatted.
lint_integ_test_calls = [
    "$geoips_repopath/tests/utils/check_code.sh all $geoips_repopath",
    "$geoips_repopath/docs/build_docs.sh $geoips_repopath $geoips_pkgname html_only",
]

# This includes ALL test scripts within the geoips repo itself with available data,
# excluding the tests under base and lint markers.
# This test list should NOT require/test anything in any other plugin package.
full_integ_test_calls = [
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
    "$geoips_repopath/tests/scripts/amsr2_rss.tc.windspeed.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/amsr2.config_based_overlay_output.sh",
    "$geoips_repopath/tests/scripts/amsr2.config_based_overlay_output_low_memory.sh",
    "$geoips_repopath/tests/scripts/amsua_mhs_mirs.tc.rainrate.imagery.sh",
    "$geoips_repopath/tests/scripts/ascat_knmi.tc.windbarbs.imagery_windbarbs_clean.sh",
    "$geoips_repopath/tests/scripts/ascat_low_knmi.tc.windbarbs.imagery_windbarbs.sh",
    "$geoips_repopath/tests/scripts/ascat_noaa_25km.tc.windbarbs.imagery_windbarbs.sh",
    (
        "$geoips_repopath/tests/scripts/"
        "ascat_noaa_50km.tc.wind-ambiguities.imagery_windbarbs.sh"
    ),
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
    (
        "$geoips_repopath/tests/scripts/"
        "seviri.WV-Upper.no_self_register.unprojected_image.sh"
    ),
    (
        "$geoips_repopath/tests/scripts/"
        "viirsclearnight.Night-Vis-IR-GeoIPS1.unprojected_image.sh"
    ),
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


def check_base_install():
    """
    Run the base installation check script to verify the GeoIPS installation.

    Executes the 'base_install.sh' script located in the GeoIPS tests directory
    to ensure that all required components are properly installed.

    Raises
    ------
    subprocess.CalledProcessError
        If the installation check script returns a non-zero exit status.
    """
    cmd = [
        "bash",
        os.path.join(
            os.getenv("GEOIPS_PACKAGES_DIR"),
            "geoips/tests/integration_tests/base_install.sh",
        ),
        "exit_on_missing",
        "skip_create_registries",
    ]
    # print("Running base install check")
    script_name = "base_install.sh"
    log_fname = set_log_filename([script_name])
    retval, stdout, stderr = call_cmd(
        cmd, output_log_fname=log_fname, use_logging=False, use_print=False
    )
    if retval != 0:
        print(f"\nCall to '{script_name}' failed, exiting")
        print("See error output in log:")
        print(f"Log: {log_fname}")
        raise RuntimeError(
            f"{script_name} failed, please see error output in log {log_fname}\n"
        )


def check_full_install():
    """
    Run the full installation check script to verify the GeoIPS installation.

    Executes the 'full_install.sh' script located in the GeoIPS tests directory
    to ensure that all required components are properly installed.

    Raises
    ------
    subprocess.CalledProcessError
        If the installation check script returns a non-zero exit status.
    """
    cmd = [
        "bash",
        os.path.join(
            os.getenv("GEOIPS_PACKAGES_DIR"),
            "geoips/tests/integration_tests/full_install.sh",
        ),
        "exit_on_missing",
        "skip_create_registries",
    ]
    # print("Running full install check")
    script_name = "full_install.sh"
    log_fname = set_log_filename([script_name])
    retval, stdout, stderr = call_cmd(
        cmd, output_log_fname=log_fname, use_logging=False, use_print=False
    )
    if retval != 0:
        print(f"\nCall to '{script_name}' failed, exiting")
        print("See error output in log:")
        print(f"Log: {log_fname}")
        raise RuntimeError(
            f"{script_name} failed, please see error output in log {log_fname}\n"
        )


def check_site_install():
    """
    Run the site installation check script to verify the GeoIPS installation.

    Executes the 'site_install.sh' script located in the GeoIPS tests directory
    to ensure that all required components are properly installed.

    Raises
    ------
    subprocess.CalledProcessError
        If the installation check script returns a non-zero exit status.
    """
    cmd = [
        "bash",
        os.path.join(
            os.getenv("GEOIPS_PACKAGES_DIR"),
            "geoips/tests/integration_tests/site_install.sh",
        ),
        "exit_on_missing",
        "skip_create_registries",
    ]
    # print("Running site install check")
    script_name = "site_install.sh"
    log_fname = set_log_filename([script_name])
    retval, stdout, stderr = call_cmd(
        cmd, output_log_fname=log_fname, use_logging=False, use_print=False
    )
    if retval != 0:
        print(f"\nCall to '{script_name}' failed, exiting")
        print("See error output in log:")
        print(f"Log: {log_fname}")
        raise RuntimeError(
            f"{script_name} failed, please see error output in log {log_fname}\n"
        )


def setup_environment():
    """
    Set up necessary environment variables for integration tests.

    Configures paths and package names for the GeoIPS core and its plugins by
    setting environment variables required for the integration tests. Assumes
    that 'GEOIPS_PACKAGES_DIR' is already set in the environment.

    Notes
    -----
    The following environment variables are set:
    - geoips_repopath
    - geoips_pkgname
    """
    # Base path
    os.environ["geoips_repopath"] = os.path.realpath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )
    os.environ["geoips_pkgname"] = "geoips"

    # Environment variable for GEOIPS_PACKAGES_DIR
    geoips_packages_dir = os.getenv("GEOIPS_PACKAGES_DIR")
    if not geoips_packages_dir:
        raise EnvironmentError("GEOIPS_PACKAGES_DIR environment variable not set.")


@pytest.fixture(scope="session")
def site_setup():
    """
    Set up the site integration tests by checking install and setting env-vars.

    Calls `check_site_install()` to verify the installation and `setup_environment()`
    to set up the necessary environment variables before running integration tests.
    """
    check_site_install()


@pytest.fixture(scope="session")
def base_setup():
    """
    Set up the base integration tests by checking install and setting env-vars.

    Calls `check_base_install()` to verify the installation and `setup_environment()`
    to set up the necessary environment variables before running integration tests.
    """
    check_base_install()


@pytest.fixture(scope="session")
def full_setup():
    """
    Set up the full integration tests by checking install and setting env-vars.

    Calls `check_full_install()` to verify the installation and `setup_environment()`
    to set up the necessary environment variables before running integration tests.
    """
    check_full_install()


def is_likely_oserror_missing_file(log_contents: str) -> bool:
    """
    Check if the log contents indicate a likely OSError for a missing file.

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
    """
    Run scripts by executing specified shell commands with bash.

    If unset_output_path_env_vars is set, explicit output path env vars are unset to
    ensure clean consistent paths for test comparisons (these env vars all default
    to a consistent location if not set, so ensure they are not set so output products
    are written to a consistent location for tests).


    Parameters
    ----------
    script : str
        Shell command to executes. The command may
        contain environment variables which will be expanded before execution.

    Raises
    ------
    subprocess.CalledProcessError
        If the shell command returns a non-zero exit status.
    """
    # The print statements all appear to print AFTER the script is complete
    # And appears to not include a newline after printing the script.
    print("")
    # Unset all supported specific output path env vars to ensure consistent test
    # output locations.  These are all defaulted to GEOIPS_OUTDIRS locations in
    # geoips_utils replace paths - we want to ensure they are not set so all paths
    # are updated with the GEOIPS_OUTDIRS relative paths for test consistency across
    # installs. GEOIPS_REPLACE_OUTPUT_PATHS is set within geoips/filenames/base_paths.py
    # to a default set of supported environment variables, overridden to the
    # specified list if GEOIPS_REPLACE_OUTPUT_PATHS is set within the environment.
    # See geoips/geoips/filenames/base_paths.py for more information on
    # GEOIPS_REPLACE_OUTPUT_PATHS
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

    if ".sh" in script:
        expanded_call = shlex.split("bash " + os.path.expandvars(script))
    else:
        expanded_call = shlex.split(os.path.expandvars(script))
    # print("Running: ", script)
    # print("Expanded call: ", expanded_call)
    # print(" ".join(expanded_call))
    log_fname = set_log_filename(expanded_call[1:])

    # Note - this will not print until after the cmd is complete
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
    run_script_with_bash(script, fail_on_missing_data)


@pytest.mark.lint
@pytest.mark.integration
@pytest.mark.parametrize("script", lint_integ_test_calls)
def test_integ_lint_test_script(base_setup: None, script: str):
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
    run_script_with_bash(script, fail_on_missing_data=True)


@pytest.mark.full
@pytest.mark.spans_multiple_packages
@pytest.mark.integration
@pytest.mark.parametrize("script", multi_repo_integ_test_calls)
def test_integ_multi_repo_script(
    site_setup: None, script: str, fail_on_missing_data: bool
):
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
    run_script_with_bash(script, fail_on_missing_data)


@pytest.mark.full
@pytest.mark.integration
@pytest.mark.parametrize("script", full_integ_test_calls)
def test_integ_full_script(full_setup: None, script: str, fail_on_missing_data: bool):
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
    run_script_with_bash(script, fail_on_missing_data)


# These are required to test the full functionality of this repo, but have limited
# test dataset availability.
@pytest.mark.full
@pytest.mark.optional
@pytest.mark.integration
@pytest.mark.parametrize("script", limited_data_integ_test_calls)
def test_integ_limited_data_script(
    full_setup: None, script: str, fail_on_missing_data: bool
):
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
    run_script_with_bash(script, fail_on_missing_data)
