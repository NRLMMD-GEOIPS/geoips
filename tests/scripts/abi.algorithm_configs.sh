# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

geoips run order_based ABIAlgorithmConfig $GEOIPS_TESTDATA_DIR/test_data_abi/data/goes16_20200918_1950/* \
  retval=$?

exit $retval
