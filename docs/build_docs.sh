# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/sh
echo "WARNING: This script has been deprecated. Please start calling build_docs.py instead"
reponame=$2
# Fortran libraries sphinx build fails without realpath
repopath=`realpath $1`
save_temp_dir=$GEOIPS_OUTDIRS/scratch/docs/$reponame
curr_path=`dirname $0`
# If this is an empty directory, remove it before we start.
# build_docs.py fails with empty latest folder.
if [ -d $repopath/docs/source/releases/latest ] && [ -z "$(ls -A "$repopath/docs/source/releases/latest")" ]; then
    echo "Latest folder is empty, removing" 
    rmdir -v $repopath/docs/source/releases/latest
fi
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
