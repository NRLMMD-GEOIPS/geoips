# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/sh
echo "WARNING: This script has been deprecated. Please start calling build_docs.py instead"
reponame=$2
repopath=$1
save_temp_dir=$GEOIPS_OUTDIRS/scratch/docs/$reponame
curr_path=`dirname $0`
python3 $GEOIPS_PACKAGES_DIR/geoips/docs/build_docs.py \
  --license-url $GEOIPS_REPO_URL \
  --geoips-docs-path $GEOIPS_PACKAGES_DIR/geoips/docs/ \
  --output-dir "$GEOIPS_PACKAGES_DIR/$2/docs/build/sphinx/html" \
  --save-temp-dir "$save_temp_dir" \
  --force \
  --repo-path $repopath \
  $reponame
retval=$?

echo "Temporary files written to:"
echo $save_temp_dir

exit $retval
