# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Pytest file for calling integration bash scripts."""

import os
import shlex
import subprocess
import sys

import pytest

base_integ_test_calls = [
    "$geoips_repopath/tests/scripts/amsr2.config_based_no_compare.sh",
    "$geoips_repopath/tests/scripts/amsr2_ocean.tc.windspeed.imagery_clean.sh",
    # "python $GEOIPS_PACKAGES_DIR/geoips/tests/utils/test_interfaces.py",
    # this should be called directly
]

full_integ_test_calls = [
    "$geoips_repopath/tests/utils/check_code.sh all $recenter_tc_repopath",
    "$geoips_repopath/docs/build_docs.sh $geoips_repopath $geoips_pkgname html_only",
    "$geoips_repopath/docs/build_docs.sh "
    "$recenter_tc_repopath $recenter_tc_pkgname html_only",
    "$geoips_repopath/docs/build_docs.sh "
    "$data_fusion_repopath $data_fusion_pkgname html_only",
    "$geoips_repopath/docs/build_docs.sh "
    "$template_basic_plugin_repopath $template_basic_plugin_pkgname html_only",
    "$geoips_repopath/tests/scripts/abi.static.Infrared.imagery_annotated.sh",
    "$geoips_repopath/tests/scripts/abi.static.Infrared.imagery_annotated_enhanced.sh",
    "$geoips_repopath/tests/scripts/console_script_create_sector_image.sh",
    "$geoips_repopath/tests/scripts/console_script_list_available_plugins.sh",
    "$geoips_repopath/tests/scripts/abi.static.Visible.imagery_annotated.sh",
    "$geoips_repopath/tests/scripts/abi.static.nasa_dust_rgb.imagery_annotated.sh",
    "$geoips_repopath/tests/scripts/abi.config_based_output_low_memory.sh",
    "$geoips_repopath/tests/scripts/abi.config_based_output.sh",
    "$geoips_repopath/tests/scripts/ami.static.Infrared.imagery_annotated.sh",
    "$geoips_repopath/tests/scripts/ami.static.Visible.imagery_annotated.sh",
    "$geoips_repopath/tests/scripts/ami.static.mst.absdiff-IR-BD.imagery_annotated.sh",
    "$geoips_repopath/tests/scripts/ami.tc.WV.geotiff.sh",
    "$geoips_repopath/tests/scripts/ami.WV-Upper.unprojected_image.sh",
    "$geoips_repopath/tests/scripts/amsr2.global.89H-Physical.cogeotiff.sh",
    "$geoips_repopath/tests/scripts/amsr2.tc.89H-Physical.imagery_annotated.sh",
    "$geoips_repopath/tests/scripts/amsr2_rss.tc.windspeed.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/amsr2.config_based_overlay_output.sh",
    "$geoips_repopath/tests/scripts/amsr2.config_based_overlay_output_low_memory.sh",
    "$geoips_repopath/tests/scripts/ascat_knmi.tc.windbarbs.imagery_windbarbs_clean.sh",
    "$geoips_repopath/tests/scripts/ascat_low_knmi.tc.windbarbs.imagery_windbarbs.sh",
    "$geoips_repopath/tests/scripts/ascat_noaa_25km.tc.windbarbs.imagery_windbarbs.sh",
    "$geoips_repopath/tests/scripts/"
    "ascat_noaa_50km.tc.wind-ambiguities.imagery_windbarbs.sh",
    "$geoips_repopath/tests/scripts/ascat_uhr.tc.wind-ambiguities.imagery_windbarbs.sh",
    "$geoips_repopath/tests/scripts/ascat_uhr.tc.nrcs.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/ascat_uhr.tc.windbarbs.imagery_windbarbs.sh",
    "$geoips_repopath/tests/scripts/ascat_uhr.tc.windspeed.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/cli_dummy_script.sh",
    "$geoips_repopath/tests/scripts/gmi.tc.89pct.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/imerg.tc.Rain.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/oscat_knmi.tc.windbarbs.imagery_windbarbs.sh",
    "$geoips_repopath/tests/scripts/sar.tc.nrcs.imagery_annotated.sh",
    "$geoips_repopath/tests/scripts/smap.unsectored.text_winds.sh",
    "$geoips_repopath/tests/scripts/viirsday.global.Night-Vis-IR.cogeotiff_rgba.sh",
    "$geoips_repopath/tests/scripts/viirsday.tc.Night-Vis-IR.imagery_annotated.sh",
    "$geoips_repopath/tests/scripts/viirsmoon.tc.Night-Vis-GeoIPS1.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/"
    "seviri.WV-Upper.no_self_register.unprojected_image.sh",
    "$geoips_repopath/tests/scripts/"
    "viirsclearnight.Night-Vis-IR-GeoIPS1.unprojected_image.sh",
    "$recenter_tc_repopath/tests/scripts/abi.tc.Visible.imagery_clean.sh",
    "$recenter_tc_repopath/tests/scripts/amsr2.tc.color37.imagery_clean.sh",
    "$recenter_tc_repopath/tests/scripts/amsr2.tc.windspeed.imagery_clean.sh",
    "$recenter_tc_repopath/tests/scripts/ascat_uhr.tc.nrcs.imagery_clean.sh",
    "$recenter_tc_repopath/tests/scripts/ascat_uhr.tc.windbarbs.imagery_clean.sh",
    "$recenter_tc_repopath/tests/scripts/imerg.tc.Rain.imagery_clean.sh",
    "$recenter_tc_repopath/tests/scripts/metopc_knmi_125.tc.windbarbs.imagery_clean.sh",
    "$recenter_tc_repopath/tests/scripts/oscat.tc.windspeed.imagery_clean.sh",
    "$recenter_tc_repopath/tests/scripts/sar.tc.nrcs.imagery_clean.sh",
    "$recenter_tc_repopath/tests/scripts/smap.tc.windspeed.imagery_clean.sh",
    "$recenter_tc_repopath/tests/scripts/viirs.tc.Infrared-Gray.imagery_clean.sh",
    "$template_basic_plugin_repopath/tests/test_all.sh",
    "$geoips_plugin_example_repopath/tests/test_all.sh",
    "$geoips_clavrx_repopath/tests/test_all.sh",
    "$data_fusion_repopath/tests/test_all.sh",
]

extra_integration_test_calls = [
    "$geoips_repopath/tests/scripts/abi.config_based_dmw_overlay.sh",
    "$geoips_repopath/tests/scripts/abi.static.dmw.imagery_windbarbs_high.sh",
    "$geoips_repopath/tests/scripts/amsub_mirs.tc.183-3H.imagery_annotated.sh",
    "$geoips_repopath/tests/scripts/atms.tc.165H.netcdf_geoips.sh",
    "$geoips_repopath/tests/scripts/ewsg.static.Infrared.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/fci.static.Visible.imagery_annotated.sh",
    "$geoips_repopath/tests/scripts/fci.unprojected_image.Infrared.sh",
    "$geoips_repopath/tests/scripts/hy2.tc.windspeed.imagery_annotated.sh",
    "$geoips_repopath/tests/scripts/mimic_coarse.static.TPW-CIMSS.imagery_annotated.sh",
    "$geoips_repopath/tests/scripts/mimic_fine.tc.TPW-PWAT.imagery_annotated.sh",
    "$geoips_repopath/tests/scripts/modis.Infrared.unprojected_image.sh",
    "$geoips_repopath/tests/scripts/saphir.tc.183-3HNearest.imagery_annotated.sh",
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
    "$geoips_repopath/tests/scripts/smap.unsectored.text_winds.sh",
    "$geoips_repopath/tests/scripts/smos.tc.sectored.text_winds.sh",
    "$geoips_repopath/tests/scripts/ssmi.tc.37pct.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/ssmis.color91.unprojected_image.sh",
    "$geoips_repopath/tests/scripts/gfs.static.windspeed.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/gfs.static.waveheight.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/viirs.static.visible.imagery_clean.sh",
]


def check_base_install():
    """
    Run the base installation check script to verify the GeoIPS installation.

    Executes the 'base_install.sh' script located in the GeoIPS tests directory
    to ensure that all required components are properly installed.

    Raises
    ------
    subprocess.CalledProcessError
        If the full installation check script returns a non-zero exit status.
    """
    base_install_check = [
        "bash",
        os.path.join(
            os.getenv("GEOIPS_PACKAGES_DIR"),
            "geoips/tests/integration_tests/base_install.sh",
        ),
        "exit_on_missing",
    ]
    print("Running base install check")
    subprocess.check_output(base_install_check, env=os.environ.copy())


def check_full_install():
    """
    Run the full installation check script to verify the GeoIPS installation.

    Executes the 'full_install.sh' script located in the GeoIPS tests directory
    to ensure that all required components are properly installed.

    Raises
    ------
    subprocess.CalledProcessError
        If the full installation check script returns a non-zero exit status.
    """
    full_install_check = [
        "bash",
        os.path.join(
            os.getenv("GEOIPS_PACKAGES_DIR"),
            "geoips/tests/integration_tests/full_install.sh",
        ),
        "exit_on_missing",
    ]
    print("Running full install check")
    subprocess.check_output(full_install_check, env=os.environ.copy())


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
    - recenter_tc_repopath
    - recenter_tc_pkgname
    - data_fusion_repopath
    - data_fusion_pkgname
    - template_basic_plugin_repopath
    - template_basic_plugin_pkgname
    - geoips_plugin_example_repopath
    - geoips_plugin_example_pkgname
    - geoips_clavrx_repopath
    - geoips_clavrx_pkgname
    """
    # Base path
    os.environ["geoips_repopath"] = os.path.join(os.path.dirname(__file__), "..", "..")
    os.environ["geoips_pkgname"] = "geoips"

    # Environment variable for GEOIPS_PACKAGES_DIR
    geoips_packages_dir = os.getenv("GEOIPS_PACKAGES_DIR")
    if not geoips_packages_dir:
        raise EnvironmentError("GEOIPS_PACKAGES_DIR environment variable not set.")

    # Paths and package names for each plugin
    os.environ["recenter_tc_repopath"] = os.path.join(
        geoips_packages_dir, "recenter_tc"
    )
    os.environ["recenter_tc_pkgname"] = "recenter_tc"

    os.environ["data_fusion_repopath"] = os.path.join(
        geoips_packages_dir, "data_fusion"
    )
    os.environ["data_fusion_pkgname"] = "data_fusion"

    os.environ["template_basic_plugin_repopath"] = os.path.join(
        geoips_packages_dir, "template_basic_plugin"
    )
    os.environ["template_basic_plugin_pkgname"] = "my_package"

    os.environ["geoips_plugin_example_repopath"] = os.path.join(
        geoips_packages_dir, "geoips_plugin_example"
    )
    os.environ["geoips_plugin_example_pkgname"] = "geoips_plugin_example"

    os.environ["geoips_clavrx_repopath"] = os.path.join(
        geoips_packages_dir, "geoips_clavrx"
    )
    os.environ["geoips_clavrx_pkgname"] = "geoips_clavrx"


@pytest.fixture(scope="session")
def full_setup():
    """
    Set up the full integration tests by checking install and setting env-vars.

    Calls `check_full_install()` to verify the installation and `setup_environment()`
    to set up the necessary environment variables before running integration tests.
    """
    check_full_install()
    setup_environment()


@pytest.fixture(scope="session")
def base_setup():
    """
    Set up the base integration tests by checking install and setting env-vars.

    Calls `check_base_install()` to verify the installation and `setup_environment()`
    to set up the necessary environment variables before running integration tests.
    """
    check_base_install()
    setup_environment()


def run_script_with_bash(script):
    """
    Run scripts by executing specified shell commands with bash.

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
    expanded_call = shlex.split("bash " + os.path.expandvars(script))
    print("Running", script)
    try:
        subprocess.check_output(expanded_call, env=os.environ.copy())
    except subprocess.CalledProcessError as e:
        print(e.output.decode(sys.stdout.encoding))
        raise e


@pytest.mark.base
@pytest.mark.integration
@pytest.mark.parametrize("script", base_integ_test_calls)
def test_integ_base_test_script(base_setup: None, script: str):
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


@pytest.mark.full
@pytest.mark.integration
@pytest.mark.parametrize("script", full_integ_test_calls)
def test_integ_full_test_script(full_setup: None, script: str):
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
    if "ami.tc.WV.geotiff.sh" in script:
        pytest.skip("GeoTIFF test is known to fail.")
    run_script_with_bash(script)


@pytest.mark.extra
@pytest.mark.integration
@pytest.mark.parametrize("script", extra_integration_test_calls)
def test_integ_extra_test_script(full_setup: None, script: str):
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
