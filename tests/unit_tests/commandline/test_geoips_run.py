# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit test for GeoIPS CLI `run` command.

See geoips/commandline/ancillary_info/cmd_instructions.yaml for more information.
"""

from importlib.resources import files

import pytest

from tests.unit_tests.commandline.cli_top_level_tester import BaseCliTest


class TestGeoipsRun(BaseCliTest):
    """Unit Testing Class for 'geoips run' Command."""

    amsr2_config_based_args = [
        "run_procflow",
        "${GEOIPS_TESTDATA_DIR}/test_data_amsr2/data/AMSR2-MBT_v2r2_GW1_s202005180620480_e202005180759470_c202005180937100.nc",  # noqa
        "--procflow",
        "config_based",
        "--output_config",
        "${GEOIPS_PACKAGES_DIR}/geoips/tests/yaml_configs/amsr2_test_no_compare.yaml",
        "--reader_kwargs",
        '{"test_arg": "Command line config-based amsr2 test arg"}',
        "--fuse_files",
        "${GEOIPS_TESTDATA_DIR}/test_data_amsr2/bg_data/ahi_20200518_0740/*",
        "--fuse_reader",
        "ahi_hsd",
        "--fuse_reader_kwargs",
        '{"test_arg": "Command line config-based ahi test arg"}',
        "--fuse_product",
        "Infrared-Gray",
        "--fuse_resampled_read",
        "True",
    ]
    new_amsr2_config_based_args = [arg for arg in amsr2_config_based_args]
    new_amsr2_config_based_args[0] = "geoips"
    new_amsr2_config_based_args.insert(1, "run")
    new_amsr2_config_based_args.insert(2, "config_based")

    abi_static_infrared_args = [
        "run_procflow",
        "$GEOIPS_TESTDATA_DIR/test_data_noaa_aws/data/goes16/20200918/1950/*",
        "--reader_name",
        "abi_netcdf",
        "--product_name",
        "Infrared",
        "--compare_path",
        "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/abi.static.<product>.imagery_annotated",  # noqa
        "--output_formatter",
        "imagery_annotated",
        "--filename_formatter",
        "geoips_fname",
        "--resampled_read",
        "--logging_level",
        "info",
        "--sector_list",
        "goes_east",
    ]
    new_abi_static_infrared_args = [arg for arg in abi_static_infrared_args]
    new_abi_static_infrared_args[0] = "geoips"
    new_abi_static_infrared_args.insert(1, "run")
    new_abi_static_infrared_args.insert(2, "single_source")

    geo_args = [
        "data_fusion_procflow",
        "--compare_path",
        "$GEOIPS_PACKAGES_DIR/data_fusion/tests/outputs/${curr_product}_image",  # noqa
        "--filename_formatter",
        "geoips_fname",
        "--sector_list",
        "global",
        "--fusion_final_output_formatter",
        "imagery_annotated",
        "--fusion_final_product_name",
        "Blended-Infrared-Gray",
        "--fusion_final_source_name",
        "stitched",
        "--fusion_final_platform_name",
        "geo",
        "--fuse_files",
        "$GEOIPS_TESTDATA_DIR/test_data_fusion/data/goes16_20210929.0000/*",  # noqa
        "--fuse_reader_name",
        "abi_netcdf",
        "--fuse_product_name",
        "${curr_product}",
        "--fuse_dataset_name",
        "goes16",
        "--fuse_order",
        "0",
        "--fuse_files",
        "$GEOIPS_TESTDATA_DIR/test_data_fusion/data/goes17_20210929.0000/*",  # noqa
        "--fuse_reader_name",
        "abi_netcdf",
        "--fuse_product_name",
        "${curr_product}",
        "--fuse_dataset_name",
        "goes17",
        "--fuse_order",
        "1",
        "--fuse_files",
        "$GEOIPS_TESTDATA_DIR/test_data_fusion/data/himawari8_20210929.0000/*",  # noqa
        "--fuse_reader_name",
        "ahi_hsd",
        "--fuse_product_name",
        "${curr_product}",
        "--fuse_dataset_name",
        "ahi",
        "--fuse_order",
        "2",
    ]
    new_geo_args = [arg for arg in geo_args]
    new_geo_args[0] = "geoips"
    new_geo_args.insert(1, "run")
    new_geo_args.insert(2, "data_fusion")

    obp_args_workflow_name = [
        "geoips",
        "run",
        "order_based",
        "$GEOIPS_TESTDATA_DIR/test_data_noaa_aws/data/goes16/20200918/1950/*",
        "--workflow",
        "read_test_v1",
    ]
    obp_args_generated_workflow = [
        "geoips",
        "run",
        "order_based",
        "$GEOIPS_TESTDATA_DIR/test_data_noaa_aws/data/goes16/20200918/1950/*",
        "--generated",
        str(
            {
                "interface": "workflows",
                "family": "order_based",
                "name": "generated",
                "docstring": "Dynamically generated workflow plugin.",
                "spec": {
                    "steps": {
                        "reader": {
                            "kind": "reader",
                            "name": "abi_netcdf",
                            "arguments": {"variables": ["B14BT"]},
                        },
                        "output_formatter": {
                            "kind": "output_formatter",
                            "name": "unprojected_image",
                            "arguments": {"sectors": ["overcast_georing"]},
                        },
                    }
                },
            }
        ),
    ]
    obp_args_workflow_path = [
        "geoips",
        "run",
        "order_based",
        "$GEOIPS_TESTDATA_DIR/test_data_noaa_aws/data/goes16/20200918/1950/*",
        "--filepath",
        f"{files('geoips') / 'plugins/yaml/workflows/read_test_v1.yaml'}",
    ]

    @property
    def command_combinations(self):
        """A stochastic list of commands used by the GeoipsRun command.

        This includes failing cases as well.
        """
        if not hasattr(self, "_cmd_list"):
            self._cmd_list = []
            base_args = ["geoips", "run"]
            # add argument lists for legacy calls 'run_procflow' and
            # 'data_fusion_procflow'
            # additionally add argument lists for 'geoips run config_based',
            # 'geoips run data_fusion', and 'geoips run single_source'

            self._cmd_list.append(self.amsr2_config_based_args)
            self._cmd_list.append(self.new_amsr2_config_based_args)
            self._cmd_list.append(self.abi_static_infrared_args)
            self._cmd_list.append(self.new_abi_static_infrared_args)
            self._cmd_list.append(self.obp_args_workflow_name)
            self._cmd_list.append(self.obp_args_generated_workflow)
            self._cmd_list.append(self.obp_args_workflow_path)
            if "data_fusion" in self.plugin_package_names:
                # Only add these argument lists if data_fusion is installed
                self._cmd_list.append(self.geo_args)
                self._cmd_list.append(self.new_geo_args)

            # Add argument list to retrieve help message
            self._cmd_list.append(["run_procflow", "-h"])
            self._cmd_list.append(base_args + ["-h"])
            self._cmd_list.append(base_args + ["config_based", "-h"])
            self._cmd_list.append(base_args + ["order_based", "-h"])
            self._cmd_list.append(base_args + ["single_source", "-h"])
            if "data_fusion" in self.plugin_package_names:
                # Only add these argument lists if data_fusion is installed
                # Doing this as a separate conditional to keep the arg-lists in order
                self._cmd_list.append(["data_fusion_procflow", "-h"])
                self._cmd_list.append(base_args + ["data_fusion", "-h"])
            # Add argument list with non existent arguments
            self._cmd_list.append(base_args + ["not_a_procflow"])
        return self._cmd_list

    def check_error(self, args, error):
        """Ensure that the 'geoips run ...' error output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI (expected to fail)
        error: str
            - Multiline str representing the error output of the CLI call
        """
        # An error occurred using args. Assert that args is not valid and check the
        # output of the error.
        assert (
            "To use, type `geoips run" in error
            or "'geoips run' was called alongside procflow:" in error
        )

    def check_output(self, args, output):
        """Ensure that the 'geoips run ...' successful output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI
        output: str
            - Multiline str representing the output of the CLI call
        """
        # The args provided are valid, so test that the output is actually correct
        if "-h" in args and len(args) <= 4:
            assert "To use, type `geoips run" in output
        else:
            # Checking that output from geoips run command reports succeeds
            if "single_source" in args:
                assert "Starting single_source procflow..." in output
            if "order_based" in args:
                assert "Begin processing" in output and "workflow" in output
            elif "config_based" in args:
                assert "Starting config_based procflow..."
            elif "data_fusion" in args:
                assert "Starting data_fusion procflow..." in output


test_sub_cmd = TestGeoipsRun()


@pytest.mark.parametrize(
    "args",
    test_sub_cmd.command_combinations,
    ids=test_sub_cmd.generate_id,
)
def test_command_combinations(monkeypatch, args):
    """Test all 'geoips run ...' commands.

    This test covers every valid combination of commands for the 'geoips run'
    command. We also test invalid commands, to ensure that the proper help documentation
    is provided for those using the command incorrectly.

    Parameters
    ----------
    args: 2D array of str
        - List of arguments to call the CLI with (ie. ['geoips', 'run'])
    """
    test_sub_cmd.test_command_combinations(monkeypatch, args)
