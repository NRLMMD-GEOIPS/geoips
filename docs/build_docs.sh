# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/sh
echo "WARNING: This script has been deprecated. Please start calling build_docs.py instead"
python3 $GEOIPS_PACKAGES_DIR/geoips/docs/build_docs.py --license-url $GEOIPS_REPO_URL --geoips-docs-path $GEOIPS_PACKAGES_DIR/$2/docs --output-dir "$GEOIPS_PACKAGES_DIR/$2/docs/build/sphinx/html" $1 $2



