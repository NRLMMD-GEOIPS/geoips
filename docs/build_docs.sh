# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/sh
python3 build_docs.py --license-url $GEOIPS_REPO_URL --geoips-docs-path $GEOIPS_PACKAGES_DIR/$2/docs --output-dir $GEOIPS_PACKAGES_DIR/$2/build $1 $2



