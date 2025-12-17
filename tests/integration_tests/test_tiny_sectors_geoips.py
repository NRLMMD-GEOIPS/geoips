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
    ##################################################################################
    # ### Scripts to produce global imagery outputs specifically for diagnostic
    # ### purposes, and identifying day/night/spatial contents of a given dataset.
    # ###
    # ### The below script will automatically run the following products
    # ###   * Test-*-Day-Night
    # ###   * Test-*-Day-Only
    # ###   * Test-*-Night-Only
    # ###
    # ### With satellite zenith cutoff of
    # ###   * 70
    # ###   * null
    # ###
    # ### Reprojected to a global domain in an annotated imagery output.
    # ###
    # ### Available product names can be found in
    # ### geoips/plugins/yaml/products/integration_tests/Test-Day-Night.yaml
    # ### geoips/plugins/yaml/products/integration_tests/Test-Day-Only.yaml
    # ### geoips/plugins/yaml/products/integration_tests/Test-Night-Only.yaml
    # ###
    # ### Product prefix should be passed below as Test-SENSOR-VAR
    ##################################################################################
    # MSG-3, METEOSAT-10, METEO-EU dataset, this dataset is nearly all day.
    # Note we have no currently available METEO-IO dataset (MSG-1 or 2)
    (
        "$geoips_repopath/tests/example_scripts/global_terminator_satzen.sh "
        "seviri_hrit "
        "Test-SEVIRI-B9 "
        "$GEOIPS_TESTDATA_DIR/test_data_seviri/data/20250624/1200/H-000-MSG3* "
    ),
    (
        "$geoips_repopath/tests/example_scripts/global_terminator_satzen.sh "
        "ami_netcdf "
        "Test-AMI-11p2 "
        "$GEOIPS_TESTDATA_DIR/test_data_ami/data/20231208_0300_daytime/gk2a_ami_le1b_*.nc"  # noqa: E501
    ),
    # MTG-I1, METEOSAT-12, METEO-EU dataset, this dataset is nearly all day.
    (
        "$geoips_repopath/tests/example_scripts/global_terminator_satzen.sh "
        "fci_netcdf "
        "Test-FCI-B14 "
        "$GEOIPS_TESTDATA_DIR/test_data_fci/data/20250623/1200/W_XX-*.nc"
    ),
    (
        "$geoips_repopath/tests/example_scripts/global_terminator_satzen.sh "
        "ahi_hsd "
        "Test-AHI-B13 "
        "$GEOIPS_TESTDATA_DIR/test_data_ahi/data/20200405_0000/HS_H08*"  # noqa: E501
    ),
    (
        "$geoips_repopath/tests/example_scripts/global_terminator_satzen.sh "
        "abi_netcdf "
        "Test-ABI-B14 "
        "${GEOIPS_TESTDATA_DIR}/test_data_abi/data/goes16_20200918_1950/OR_ABI-L1b*_G16_*.nc"  # noqa: E501
    ),
    (
        "$geoips_repopath/tests/example_scripts/global_terminator_satzen.sh "
        "abi_netcdf "
        "Test-ABI-B14 "
        "$GEOIPS_TESTDATA_DIR/test_data_abi/data/goes17_20210718_0150/OR_ABI-L1b*_G17_*.nc"  # noqa: E501
    ),
]

tiny_sector_overlay_integ_test_calls = [
    ##################################################################################
    # ### Output geoips test sector overlays on a global map to identify location of
    # ### each defined tiny sector.  Used for diagnostic purposes to evaluate location
    # ### and size of each tiny sector.
    ##################################################################################
    ##################################################################################
    # ### Satellite specific test sectors, not reliant on a specific dataset
    ##################################################################################
    "geoips test sector --overlay test_goeswest_eqc_3km_nadir -o $GEOIPS_OUTDIRS/example_test_imagery_outputs ",  # noqa: E501
    "geoips test sector --overlay test_goeswest_eqc_3km_landocean -o $GEOIPS_OUTDIRS/example_test_imagery_outputs ",  # noqa: E501
    "geoips test sector --overlay test_goeswest_longlat_50km_fulldisk -o $GEOIPS_OUTDIRS/example_test_imagery_outputs ",  # noqa: E501
    "geoips test sector --overlay test_goeseast_eqc_3km_nadir -o $GEOIPS_OUTDIRS/example_test_imagery_outputs ",  # noqa: E501
    "geoips test sector --overlay test_goeseast_eqc_3km_landocean -o $GEOIPS_OUTDIRS/example_test_imagery_outputs ",  # noqa: E501
    "geoips test sector --overlay test_goeseast_longlat_50km_fulldisk -o $GEOIPS_OUTDIRS/example_test_imagery_outputs ",  # noqa: E501
    "geoips test sector --overlay test_himawari_eqc_3km_landocean -o $GEOIPS_OUTDIRS/example_test_imagery_outputs ",  # noqa: E501
    "geoips test sector --overlay test_meteoeu_eqc_3km_landocean -o $GEOIPS_OUTDIRS/example_test_imagery_outputs ",  # noqa: E501
    "geoips test sector --overlay test_meteoeu_longlat_50km_fulldisk -o $GEOIPS_OUTDIRS/example_test_imagery_outputs ",  # noqa: E501
    "geoips test sector --overlay test_meteoio_eqc_3km_landocean -o $GEOIPS_OUTDIRS/example_test_imagery_outputs ",  # noqa: E501
    "geoips test sector --overlay test_meteoio_longlat_50km_fulldisk -o $GEOIPS_OUTDIRS/example_test_imagery_outputs ",  # noqa: E501
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
    "geoips test sector --overlay test_himawari8_eqc_10km_terminator_20200405T0000Z -o $GEOIPS_OUTDIRS/example_test_imagery_outputs ",  # noqa: E501
]

tiny_sector_integ_test_calls = [
    ##################################################################################
    # ### Test the actual output of each specified tiny sector defined within this repo.
    # ### tiny_sectors_geostationary.sh is a wrapper test script to produce the
    # ### specified tiny sector output, and compare it with the stored comparison
    # ### output imagery.
    # ###
    # ### It always produces
    # ### * imagery_clean output
    # ### * geoips_fname filename formatter,
    # ### * --compare_path "$GEOIPS_PACKAGES_DIR/${repo_name}/tests/integration_tests/tiny_sectors/outputs/${test_sector_name}_${product_name}"   # noqa: E501
    # ### * satellite zenith angle cutoff None,
    # ###
    # ### with the following arguments passed in:
    # ###
    # ### * test_sector_name
    # ###   * Usually of format test_SATELLITE_PROJ_RES_FEAT_DAYNIGHT_YYYYMMDDTHHMNZ
    # ###   * e.g. test_goes16_eqc_3km_edge_day_20200918T1950Z
    # ###   * e.g. test_goeswest_eqc_3km_nadir
    # ### * reader_name
    # ### * product_name
    # ###   * Test-*-Day-Only, or -Night-Only for efficiency
    # ###     reasons, consistency, and quickly identifying
    # ###     the terminator location
    # ### * repo_name
    # ### * data_files
    # ###
    # ### Available product names of the format Test-SENSOR-Var-* can be found in
    # ### geoips/plugins/yaml/products/integration_tests/Test-Day-Night.yaml
    # ### geoips/plugins/yaml/products/integration_tests/Test-Day-Only.yaml
    # ### geoips/plugins/yaml/products/integration_tests/Test-Night-Only.yaml
    # ###
    # ### NOTE if you set the environment variable
    # ### export GEOIPS_CREATE_TINY_SECTOR_TEST_GEOTIFF_OUTPUTS=True
    # ### then tiny_sectors_geostationary.sh will produce a geotiff output (with
    # ### no image output comparison) for evaluation / reference purposes, in addition
    # ### to the imagery_clean output that is used in the required integration tests.
    # ### This environment variable can be used for evaluation/reference purposes.
    ##################################################################################
    ##################################################################################
    # ### Satellite specific test sectors, not reliant on a specific dataset
    ##################################################################################
    # Tiny sectors for GOES-EAST nadir
    (
        "$geoips_repopath/tests/integration_tests/tiny_sectors/tiny_sectors_geostationary.sh "  # noqa: E501
        "test_goeseast_eqc_3km_nadir "
        "abi_netcdf "
        "Test-ABI-B14-Day-Night "
        "geoips "
        "$GEOIPS_TESTDATA_DIR/test_data_abi/data/goes16_20200918_1950/OR_ABI-L1b*.nc"
    ),
    # Tiny sectors for GOES-EAST landocean
    (
        "$geoips_repopath/tests/integration_tests/tiny_sectors/tiny_sectors_geostationary.sh "  # noqa: E501
        "test_goeseast_eqc_3km_landocean "
        "abi_netcdf "
        "Test-ABI-B14-Day-Night "
        "geoips "
        "$GEOIPS_TESTDATA_DIR/test_data_abi/data/goes16_20200918_1950/OR_ABI-L1b*.nc"
    ),
    # Tiny sectors for GOES-EAST longlat full disk
    (
        "$geoips_repopath/tests/integration_tests/tiny_sectors/tiny_sectors_geostationary.sh "  # noqa: E501
        "test_goeseast_longlat_50km_fulldisk "
        "abi_netcdf "
        "Test-ABI-B14-Day-Night "
        "geoips "
        "$GEOIPS_TESTDATA_DIR/test_data_abi/data/goes16_20200918_1950/OR_ABI-L1b*.nc"
    ),
    # Tiny sectors for GOES-WEST nadir
    (
        "$geoips_repopath/tests/integration_tests/tiny_sectors/tiny_sectors_geostationary.sh "  # noqa: E501
        "test_goeswest_eqc_3km_nadir "
        "abi_netcdf "
        "Test-ABI-B14-Day-Night "
        "geoips "
        "$GEOIPS_TESTDATA_DIR/test_data_abi/data/goes17_20210718_0150/OR_ABI-L1b*.nc"
    ),
    # Tiny sectors for GOES-WEST landocean
    (
        "$geoips_repopath/tests/integration_tests/tiny_sectors/tiny_sectors_geostationary.sh "  # noqa: E501
        "test_goeswest_eqc_3km_landocean "
        "abi_netcdf "
        "Test-ABI-B14-Day-Night "
        "geoips "
        "$GEOIPS_TESTDATA_DIR/test_data_abi/data/goes17_20210718_0150/OR_ABI-L1b*.nc"
    ),
    # Tiny sectors for GOES-WEST longlat full disk
    (
        "$geoips_repopath/tests/integration_tests/tiny_sectors/tiny_sectors_geostationary.sh "  # noqa: E501
        "test_goeswest_longlat_50km_fulldisk "
        "abi_netcdf "
        "Test-ABI-B14-Day-Night "
        "geoips "
        "$GEOIPS_TESTDATA_DIR/test_data_abi/data/goes17_20210718_0150/OR_ABI-L1b*.nc"
    ),
    # Tiny sectors for Himawari landocean
    (
        "$geoips_repopath/tests/integration_tests/tiny_sectors/tiny_sectors_geostationary.sh "  # noqa: E501
        "test_himawari_eqc_3km_landocean "
        "ahi_hsd "
        "Test-AHI-B13-Day-Only "
        "geoips "
        "$GEOIPS_TESTDATA_DIR/test_data_ahi/data/20200405_0000/*"
    ),
    # Tiny sectors for MeteoEU landocean, using FCI MTG-I1 dataset
    (
        "$geoips_repopath/tests/integration_tests/tiny_sectors/tiny_sectors_geostationary.sh "  # noqa: E501
        "test_meteoeu_eqc_3km_landocean "
        "fci_netcdf "
        "Test-FCI-B14-Day-Only "
        "geoips "
        "$GEOIPS_TESTDATA_DIR/test_data_fci/data/20250623/1200/W_XX-*.nc"
    ),
    # Tiny sectors for MeteoEU longlat full disk, using SEVIRI MSG3 dataset
    (
        "$geoips_repopath/tests/integration_tests/tiny_sectors/tiny_sectors_geostationary.sh "  # noqa: E501
        "test_meteoeu_longlat_50km_fulldisk "
        "seviri_hrit "
        "Test-SEVIRI-B9-Day-Only "
        "geoips "
        "$GEOIPS_TESTDATA_DIR/test_data_seviri/data/20250624/1200/H-000-MSG3* "
    ),
    # No MeteoIO test dataset currently
    ##################################################################################
    # ### Dataset specific test sectors, reliant on specific time of day and/or
    # ### meteorological features within the dataset.
    ##################################################################################
    # Tiny sectors for GOES-16 edge day
    (
        "$geoips_repopath/tests/integration_tests/tiny_sectors/tiny_sectors_geostationary.sh "  # noqa: E501
        "test_goes16_eqc_10km_edge_day_20200918T1950Z "
        "abi_netcdf "
        "Test-ABI-B14-Day-Only "
        "geoips "
        "$GEOIPS_TESTDATA_DIR/test_data_abi/data/goes16_20200918_1950/OR_ABI-L1b*.nc"
    ),
    # Tiny sectors for GOES-16 edge night
    (
        "$geoips_repopath/tests/integration_tests/tiny_sectors/tiny_sectors_geostationary.sh "  # noqa: E501
        "test_goes16_eqc_10km_edge_night_20200918T1950Z "
        "abi_netcdf "
        "Test-ABI-B14-Night-Only "
        "geoips "
        "$GEOIPS_TESTDATA_DIR/test_data_abi/data/goes16_20200918_1950/OR_ABI-L1b*.nc"
    ),
    # Tiny sectors for GOES-16  day
    (
        "$geoips_repopath/tests/integration_tests/tiny_sectors/tiny_sectors_geostationary.sh "  # noqa: E501
        "test_goes16_eqc_3km_day_20200918T1950Z "
        "abi_netcdf "
        "Test-ABI-B14-Day-Only "
        "geoips "
        "$GEOIPS_TESTDATA_DIR/test_data_abi/data/goes16_20200918_1950/OR_ABI-L1b*.nc"
    ),
    # Tiny sectors for GOES-16  night
    (
        "$geoips_repopath/tests/integration_tests/tiny_sectors/tiny_sectors_geostationary.sh "  # noqa: E501
        "test_goes16_eqc_3km_night_20200918T1950Z "
        "abi_netcdf "
        "Test-ABI-B14-Night-Only "
        "geoips "
        "$GEOIPS_TESTDATA_DIR/test_data_abi/data/goes16_20200918_1950/OR_ABI-L1b*.nc"
    ),
    # Tiny sectors for GOES-16 terminator
    (
        "$geoips_repopath/tests/integration_tests/tiny_sectors/tiny_sectors_geostationary.sh "  # noqa: E501
        "test_goes16_eqc_3km_terminator_20200918T1950Z "
        "abi_netcdf "
        "Test-ABI-B14-Day-Only "
        "geoips "
        "$GEOIPS_TESTDATA_DIR/test_data_abi/data/goes16_20200918_1950/OR_ABI-L1b*.nc"
    ),
    # Tiny sectors for GOES-17 edge night
    (
        "$geoips_repopath/tests/integration_tests/tiny_sectors/tiny_sectors_geostationary.sh "  # noqa: E501
        "test_goes17_eqc_10km_edge_night_20210718T0150Z "
        "abi_netcdf "
        "Test-ABI-B14-Night-Only "
        "geoips "
        "$GEOIPS_TESTDATA_DIR/test_data_abi/data/goes17_20210718_0150/OR_ABI-L1b*.nc"
    ),
    # Tiny sectors for GOES-17 edge day
    (
        "$geoips_repopath/tests/integration_tests/tiny_sectors/tiny_sectors_geostationary.sh "  # noqa: E501
        "test_goes17_eqc_10km_edge_day_20210718T0150Z "
        "abi_netcdf "
        "Test-ABI-B14-Day-Only "
        "geoips "
        "$GEOIPS_TESTDATA_DIR/test_data_abi/data/goes17_20210718_0150/OR_ABI-L1b*.nc"
    ),
    # Tiny sectors for GOES-17  night
    (
        "$geoips_repopath/tests/integration_tests/tiny_sectors/tiny_sectors_geostationary.sh "  # noqa: E501
        "test_goes17_eqc_3km_night_20210718T0150Z "
        "abi_netcdf "
        "Test-ABI-B14-Night-Only "
        "geoips "
        "$GEOIPS_TESTDATA_DIR/test_data_abi/data/goes17_20210718_0150/OR_ABI-L1b*.nc"
    ),
    # Tiny sectors for GOES-17  day
    (
        "$geoips_repopath/tests/integration_tests/tiny_sectors/tiny_sectors_geostationary.sh "  # noqa: E501
        "test_goes17_eqc_3km_day_20210718T0150Z "
        "abi_netcdf "
        "Test-ABI-B14-Day-Only "
        "geoips "
        "$GEOIPS_TESTDATA_DIR/test_data_abi/data/goes17_20210718_0150/OR_ABI-L1b*.nc"
    ),
    # Tiny sectors for GOES-17 terminator
    (
        "$geoips_repopath/tests/integration_tests/tiny_sectors/tiny_sectors_geostationary.sh "  # noqa: E501
        "test_goes17_eqc_3km_terminator_20210718T0150Z "
        "abi_netcdf "
        "Test-ABI-B14-Day-Only "
        "geoips "
        "$GEOIPS_TESTDATA_DIR/test_data_abi/data/goes17_20210718_0150/OR_ABI-L1b*.nc"
    ),
    # Tiny sector for Himawari terminator
    (
        "$geoips_repopath/tests/integration_tests/tiny_sectors/tiny_sectors_geostationary.sh "  # noqa: E501
        "test_himawari8_eqc_10km_terminator_20200405T0000Z "
        "ahi_hsd "
        "Test-AHI-B13-Day-Only "
        "geoips "
        "$GEOIPS_TESTDATA_DIR/test_data_ahi/data/20200405_0000/*"
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
    os.environ["repopath"] = os.path.realpath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )
    os.environ["pkgname"] = "geoips"


@pytest.mark.optional
@pytest.mark.sample_output
@pytest.mark.tiny_sector_evaluation
@pytest.mark.tiny_sector_global_example
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
    setup_environment()
    run_script_with_bash(script)


@pytest.mark.optional
@pytest.mark.sample_output
@pytest.mark.tiny_sector_evaluation
@pytest.mark.tiny_sector_overlay
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
    setup_environment()
    run_script_with_bash(script)


@pytest.mark.optional
@pytest.mark.full
@pytest.mark.integration
@pytest.mark.tiny_sector_evaluation
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
    setup_environment()
    run_script_with_bash(script)
