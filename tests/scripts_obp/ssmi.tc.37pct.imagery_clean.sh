# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

# cspell:ignore bdecks cfnoc sdrmi tdrmi

geoips run order_based -w   \
          $GEOIPS_TESTDATA_DIR/test_data_ssmi/data/US058SORB-DEFspp.sdrmi_f15_d20200519_s080800_e095300_r05633_cfnoc.def \
          $GEOIPS_TESTDATA_DIR/test_data_ssmi/data/US058SORB-DEFspp.tdrmi_f15_d20200519_s080800_e095300_r05633_cfnoc.def \

exit $?
