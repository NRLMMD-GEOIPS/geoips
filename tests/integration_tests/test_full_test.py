# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

import os
import subprocess
import pytest
import sys

integ_test_calls = [
    "$geoips_repopath/tests/utils/check_code.sh all $recenter_tc_repopath",
    "$geoips_repopath/docs/build_docs.sh $geoips_repopath $geoips_pkgname html_only",
    "$geoips_repopath/docs/build_docs.sh $recenter_tc_repopath $recenter_tc_pkgname html_only",
    "$geoips_repopath/docs/build_docs.sh $data_fusion_repopath $data_fusion_pkgname html_only",
    "$geoips_repopath/docs/build_docs.sh $template_basic_plugin_repopath $template_basic_plugin_pkgname html_only",
    "$geoips_repopath/tests/scripts/abi.static.Infrared.imagery_annotated.sh",
    "$geoips_repopath/tests/scripts/console_script_create_sector_image.sh",
    "$geoips_repopath/tests/scripts/console_script_list_available_plugins.sh",
    "$geoips_repopath/tests/scripts/abi.static.Visible.imagery_annotated.sh",
    "$geoips_repopath/tests/scripts/abi.config_based_output_low_memory.sh",
    "$geoips_repopath/tests/scripts/abi.config_based_output.sh",
    "$geoips_repopath/tests/scripts/ahi.tc.WV.geotiff.sh",
    "$geoips_repopath/tests/scripts/ami.static.Infrared.imagery_annotated.sh",
    "$geoips_repopath/tests/scripts/ami.static.Visible.imagery_annotated.sh",
    "$geoips_repopath/tests/scripts/ami.tc.WV.geotiff.sh",
    "$geoips_repopath/tests/scripts/ami.WV-Upper.unprojected_image.sh",
    "$geoips_repopath/tests/scripts/amsr2.tc.89H-Physical.imagery_annotated.sh",
    "$geoips_repopath/tests/scripts/amsr2_ocean.tc.windspeed.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/amsr2.config_based_no_compare.sh",
    "$geoips_repopath/tests/scripts/amsr2.config_based_overlay_output.sh",
    "$geoips_repopath/tests/scripts/amsr2.config_based_overlay_output_low_memory.sh",
    "$geoips_repopath/tests/scripts/ascat_knmi.tc.windbarbs.imagery_windbarbs_clean.sh",
    "$geoips_repopath/tests/scripts/ascat_low_knmi.tc.windbarbs.imagery_windbarbs.sh",
    "$geoips_repopath/tests/scripts/ascat_noaa_25km.tc.windbarbs.imagery_windbarbs.sh",
    "$geoips_repopath/tests/scripts/ascat_noaa_50km.tc.wind-ambiguities.imagery_windbarbs.sh",
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
    "$geoips_repopath/tests/scripts/viirsday.tc.Night-Vis-IR.imagery_annotated.sh",
    "$geoips_repopath/tests/scripts/viirsmoon.tc.Night-Vis-GeoIPS1.imagery_clean.sh",
    "$geoips_repopath/tests/scripts/viirsclearnight.Night-Vis-IR-GeoIPS1.unprojected_image.sh",
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


def check_full_install():
    full_install_check = [
        "bash",
        os.getenv("GEOIPS_PACKAGES_DIR")
        + "/geoips/tests/integration_tests/full_install.sh",
        "exit_on_missing",
    ]
    print("Running full install check")
    subprocess.check_output(full_install_check, env=os.environ.copy())


def setup_environment():
    # Base path
    os.environ["geoips_repopath"] = os.path.join(os.path.dirname(__file__), "..", "..")
    os.environ["geoips_pkgname"] = "geoips"

    # Environment variable for geoips_packages_dir (assuming it is already set in your environment)
    geoips_packages_dir = os.getenv("GEOIPS_PACKAGES_DIR")

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


integ_tests_setup = False


def setup_integ_tests():
    check_full_install()
    setup_environment()
    global integ_tests_setup
    integ_tests_setup = True


@pytest.mark.integration
@pytest.mark.parametrize("script", integ_test_calls)
def test_integ_test_script(script):
    if not integ_tests_setup:
        setup_integ_tests()
    expanded_call = ("bash " + os.path.expandvars(script)).split(" ")
    print("Running", script)
    try:
        subprocess.check_output(expanded_call, env=os.environ.copy())
    except subprocess.CalledProcessError as e:
        print(e.output.decode(sys.stdout.encoding))
        raise e
