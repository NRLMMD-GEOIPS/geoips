# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Pytest file for calling integration bash scripts."""

import os
import pytest

from tests.integration_tests.test_integration import base_setup  # noqa: F401

from tests.integration_tests.test_integration import (
    run_script_with_bash,
    setup_environment as setup_geoips_environment,
)

global_example_integ_test_calls = [
    # Run all pre-set examples for global_terminator_satzen.sh (quick look at locations
    # of all satellites)
    "$geoips_repopath/tests/example_scripts/global_terminator_satzen.sh all",
    # The below are already in the pre-set examples. We only want to run additional
    # datasets beyond the pre-set examples.  We'll leave these in here commented out to
    # identify these as the pre-set examples, so if we have any additional datasets
    # besides these, we can add them as individual calls.  We just do not want to
    # duplicate processing for the examples that are already in
    # global_terminator_satzen.sh
    # $GEOIPS_TESTDATA_DIR/test_data_ahi/data/20200405_0000/HS_H08* \
    # $GEOIPS_TESTDATA_DIR/test_data_fci/data/mt1_fdhsi_20240113_1150/* \
    # $GEOIPS_TESTDATA_DIR/test_data_ami/data/20231208_0300_daytime/gk2a_ami_le1b_*.nc \
    # $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20200404.0800_meteoIO_tc2020sh24irondro/*MSG1_IODC* \  # noqa: E501
    # ${GEOIPS_TESTDATA_DIR}/test_data_abi/data/goes16_20200918_1950/OR_ABI-L1b*_G16_*.nc \  # noqa: E501
    # $GEOIPS_TESTDATA_DIR/test_data_abi/data/goes17_20210718_0150/OR_ABI-L1b*_G17_*.nc \  # noqa: E501
    # Formatting for individual calls, for reference when adding additional datasets
    # (
    #     "$geoips_repopath/tests/example_scripts/global_terminator_satzen.sh "
    #     "abi_netcdf "
    #     "$GEOIPS_TESTDATA_DIR/test_data_abi/data/goes16_20200918_1950/OR_ABI-L1b*.nc"
    # ),
]

tiny_sector_overlay_integ_test_calls = [
    ##################################################################################
    # ### Satellite specific test sectors, not reliant on a specific dataset
    ##################################################################################
    # Satellite specific test sectors, not reliant on a specific dataset
    "geoips test sector --overlay test_goeswest_eqc_3km_nadir -o $GEOIPS_OUTDIRS/example_test_imagery_outputs ",  # noqa: E501
    "geoips test sector --overlay test_goeswest_eqc_3km_landocean -o $GEOIPS_OUTDIRS/example_test_imagery_outputs ",  # noqa: E501
    "geoips test sector --overlay test_goeswest_longlat_50km_fulldisk -o $GEOIPS_OUTDIRS/example_test_imagery_outputs ",  # noqa: E501
    "geoips test sector --overlay test_goeseast_eqc_3km_nadir -o $GEOIPS_OUTDIRS/example_test_imagery_outputs ",  # noqa: E501
    "geoips test sector --overlay test_goeseast_eqc_3km_landocean -o $GEOIPS_OUTDIRS/example_test_imagery_outputs ",  # noqa: E501
    "geoips test sector --overlay test_goeseast_longlat_50km_fulldisk -o $GEOIPS_OUTDIRS/example_test_imagery_outputs ",  # noqa: E501
    ##################################################################################
    # ### Dataset specific test sectors, reliant on specific time of day and/or
    # ### meteorological features within the dataset.
    ##################################################################################
    "geoips test sector --overlay test_goes16_eqc_10km_edge_day_20200918T1950Z -o $GEOIPS_OUTDIRS/example_test_imagery_outputs ",  # noqa: E501
    "geoips test sector --overlay test_goes16_eqc_10km_edge_night_20200918T1950Z -o $GEOIPS_OUTDIRS/example_test_imagery_outputs ",  # noqa: E501
    "geoips test sector --overlay test_goes16_eqc_3km_day_20200918T1950Z -o $GEOIPS_OUTDIRS/example_test_imagery_outputs ",  # noqa: E501
    "geoips test sector --overlay test_goes16_eqc_3km_night_20200918T1950Z -o $GEOIPS_OUTDIRS/example_test_imagery_outputs ",  # noqa: E501
    "geoips test sector --overlay test_goes16_eqc_3km_terminator_20200918T1950Z -o $GEOIPS_OUTDIRS/example_test_imagery_outputs ",  # noqa: E501
    "geoips test sector --overlay test_goes17_eqc_10km_edge_day_20210718T0150Z -o $GEOIPS_OUTDIRS/example_test_imagery_outputs ",  # noqa: E501
    "geoips test sector --overlay test_goes17_eqc_10km_edge_night_20210718T0150Z -o $GEOIPS_OUTDIRS/example_test_imagery_outputs ",  # noqa: E501
    "geoips test sector --overlay test_goes17_eqc_3km_day_20210718T0150Z -o $GEOIPS_OUTDIRS/example_test_imagery_outputs ",  # noqa: E501
    "geoips test sector --overlay test_goes17_eqc_3km_night_20210718T0150Z -o $GEOIPS_OUTDIRS/example_test_imagery_outputs ",  # noqa: E501
    "geoips test sector --overlay test_goes17_eqc_3km_terminator_20210718T0150Z -o $GEOIPS_OUTDIRS/example_test_imagery_outputs ",  # noqa: E501
]

tiny_sector_integ_test_calls = [
    ##################################################################################
    # ### Satellite specific test sectors, not reliant on a specific dataset
    ##################################################################################
    # Tiny sectors for GOES-EAST nadir
    (
        "$geoips_repopath/tests/integration_tests/tiny_sectors/tiny_sectors_geostationary.sh "  # noqa: E501
        "test_goeseast_eqc_3km_nadir "
        "abi_netcdf "
        "Test-Infrared-Day-Night "
        "geoips "
        "$GEOIPS_TESTDATA_DIR/test_data_abi/data/goes16_20200918_1950/OR_ABI-L1b*.nc"
    ),
    # Tiny sectors for GOES-EAST landocean
    (
        "$geoips_repopath/tests/integration_tests/tiny_sectors/tiny_sectors_geostationary.sh "  # noqa: E501
        "test_goeseast_eqc_3km_landocean "
        "abi_netcdf "
        "Test-Infrared-Day-Night "
        "geoips "
        "$GEOIPS_TESTDATA_DIR/test_data_abi/data/goes16_20200918_1950/OR_ABI-L1b*.nc"
    ),
    # Tiny sectors for GOES-EAST longlat full disk
    (
        "$geoips_repopath/tests/integration_tests/tiny_sectors/tiny_sectors_geostationary.sh "  # noqa: E501
        "test_goeseast_longlat_50km_fulldisk "
        "abi_netcdf "
        "Test-Infrared-Day-Night "
        "geoips "
        "$GEOIPS_TESTDATA_DIR/test_data_abi/data/goes16_20200918_1950/OR_ABI-L1b*.nc"
    ),
    # Tiny sectors for GOES-WEST nadir
    (
        "$geoips_repopath/tests/integration_tests/tiny_sectors/tiny_sectors_geostationary.sh "  # noqa: E501
        "test_goeswest_eqc_3km_nadir "
        "abi_netcdf "
        "Test-Infrared-Day-Night "
        "geoips "
        "$GEOIPS_TESTDATA_DIR/test_data_abi/data/goes17_20210718_0150/OR_ABI-L1b*.nc"
    ),
    # Tiny sectors for GOES-WEST landocean
    (
        "$geoips_repopath/tests/integration_tests/tiny_sectors/tiny_sectors_geostationary.sh "  # noqa: E501
        "test_goeswest_eqc_3km_landocean "
        "abi_netcdf "
        "Test-Infrared-Day-Night "
        "geoips "
        "$GEOIPS_TESTDATA_DIR/test_data_abi/data/goes17_20210718_0150/OR_ABI-L1b*.nc"
    ),
    # Tiny sectors for GOES-WEST longlat full disk
    (
        "$geoips_repopath/tests/integration_tests/tiny_sectors/tiny_sectors_geostationary.sh "  # noqa: E501
        "test_goeswest_longlat_50km_fulldisk "
        "abi_netcdf "
        "Test-Infrared-Day-Night "
        "geoips "
        "$GEOIPS_TESTDATA_DIR/test_data_abi/data/goes17_20210718_0150/OR_ABI-L1b*.nc"
    ),
    ##################################################################################
    # ### Dataset specific test sectors, reliant on specific time of day and/or
    # ### meteorological features within the dataset.
    ##################################################################################
    # Tiny sectors for GOES-16 edge day
    (
        "$geoips_repopath/tests/integration_tests/tiny_sectors/tiny_sectors_geostationary.sh "  # noqa: E501
        "test_goes16_eqc_10km_edge_day_20200918T1950Z "
        "abi_netcdf "
        "Test-Infrared-Day-Only "
        "geoips "
        "$GEOIPS_TESTDATA_DIR/test_data_abi/data/goes16_20200918_1950/OR_ABI-L1b*.nc"
    ),
    # Tiny sectors for GOES-16 edge night
    (
        "$geoips_repopath/tests/integration_tests/tiny_sectors/tiny_sectors_geostationary.sh "  # noqa: E501
        "test_goes16_eqc_10km_edge_night_20200918T1950Z "
        "abi_netcdf "
        "Test-Infrared-Night-Only "
        "geoips "
        "$GEOIPS_TESTDATA_DIR/test_data_abi/data/goes16_20200918_1950/OR_ABI-L1b*.nc"
    ),
    # Tiny sectors for GOES-16  day
    (
        "$geoips_repopath/tests/integration_tests/tiny_sectors/tiny_sectors_geostationary.sh "  # noqa: E501
        "test_goes16_eqc_3km_day_20200918T1950Z "
        "abi_netcdf "
        "Test-Infrared-Day-Only "
        "geoips "
        "$GEOIPS_TESTDATA_DIR/test_data_abi/data/goes16_20200918_1950/OR_ABI-L1b*.nc"
    ),
    # Tiny sectors for GOES-16  night
    (
        "$geoips_repopath/tests/integration_tests/tiny_sectors/tiny_sectors_geostationary.sh "  # noqa: E501
        "test_goes16_eqc_3km_night_20200918T1950Z "
        "abi_netcdf "
        "Test-Infrared-Night-Only "
        "geoips "
        "$GEOIPS_TESTDATA_DIR/test_data_abi/data/goes16_20200918_1950/OR_ABI-L1b*.nc"
    ),
    # Tiny sectors for GOES-16 terminator
    (
        "$geoips_repopath/tests/integration_tests/tiny_sectors/tiny_sectors_geostationary.sh "  # noqa: E501
        "test_goes16_eqc_3km_terminator_20200918T1950Z "
        "abi_netcdf "
        "Test-Infrared-Day-Only "
        "geoips "
        "$GEOIPS_TESTDATA_DIR/test_data_abi/data/goes16_20200918_1950/OR_ABI-L1b*.nc"
    ),
    # Tiny sectors for GOES-17 edge night
    (
        "$geoips_repopath/tests/integration_tests/tiny_sectors/tiny_sectors_geostationary.sh "  # noqa: E501
        "test_goes17_eqc_10km_edge_night_20210718T0150Z "
        "abi_netcdf "
        "Test-Infrared-Night-Only "
        "geoips "
        "$GEOIPS_TESTDATA_DIR/test_data_abi/data/goes17_20210718_0150/OR_ABI-L1b*.nc"
    ),
    # Tiny sectors for GOES-17 edge day
    (
        "$geoips_repopath/tests/integration_tests/tiny_sectors/tiny_sectors_geostationary.sh "  # noqa: E501
        "test_goes17_eqc_10km_edge_day_20210718T0150Z "
        "abi_netcdf "
        "Test-Infrared-Day-Only "
        "geoips "
        "$GEOIPS_TESTDATA_DIR/test_data_abi/data/goes17_20210718_0150/OR_ABI-L1b*.nc"
    ),
    # Tiny sectors for GOES-17  night
    (
        "$geoips_repopath/tests/integration_tests/tiny_sectors/tiny_sectors_geostationary.sh "  # noqa: E501
        "test_goes17_eqc_3km_night_20210718T0150Z "
        "abi_netcdf "
        "Test-Infrared-Night-Only "
        "geoips "
        "$GEOIPS_TESTDATA_DIR/test_data_abi/data/goes17_20210718_0150/OR_ABI-L1b*.nc"
    ),
    # Tiny sectors for GOES-17  day
    (
        "$geoips_repopath/tests/integration_tests/tiny_sectors/tiny_sectors_geostationary.sh "  # noqa: E501
        "test_goes17_eqc_3km_day_20210718T0150Z "
        "abi_netcdf "
        "Test-Infrared-Day-Only "
        "geoips "
        "$GEOIPS_TESTDATA_DIR/test_data_abi/data/goes17_20210718_0150/OR_ABI-L1b*.nc"
    ),
    # Tiny sectors for GOES-17 terminator
    (
        "$geoips_repopath/tests/integration_tests/tiny_sectors/tiny_sectors_geostationary.sh "  # noqa: E501
        "test_goes17_eqc_3km_terminator_20210718T0150Z "
        "abi_netcdf "
        "Test-Infrared-Day-Only "
        "geoips "
        "$GEOIPS_TESTDATA_DIR/test_data_abi/data/goes17_20210718_0150/OR_ABI-L1b*.nc"
    ),
]


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
    - repopath
    - pkgname
    """
    # Setup base geoips environment
    setup_geoips_environment()
    # Setup current repo's environment
    os.environ["repopath"] = os.path.join(os.path.dirname(__file__), "..", "..")
    os.environ["pkgname"] = "geoips"


@pytest.mark.optional
@pytest.mark.full
@pytest.mark.sample_output
@pytest.mark.parametrize("script", global_example_integ_test_calls)
def test_integ_global_example_script(base_setup: None, script: str):  # noqa: F811
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
    run_script_with_bash(script)


@pytest.mark.optional
@pytest.mark.full
@pytest.mark.tiny_sector
@pytest.mark.sample_output
@pytest.mark.parametrize("script", tiny_sector_overlay_integ_test_calls)
def test_integ_tiny_sector_overlay_script(base_setup: None, script: str):  # noqa: F811
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
    run_script_with_bash(script)


@pytest.mark.optional
@pytest.mark.full
@pytest.mark.integration
@pytest.mark.tiny_sector
@pytest.mark.parametrize("script", tiny_sector_integ_test_calls)
def test_integ_tiny_sector_script(base_setup: None, script: str):  # noqa: F811
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
    run_script_with_bash(script)
