# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

if [[ "$1" == "" ]]; then
    echo ""
    echo "Usage: $0 <repo_name>"
    echo ""
    echo "Where <repo_name> either"
    echo "    $GEOIPS_PACKAGES_DIR/<repo_name>"
    echo "    $GEOIPS_TESTDATA_DIR/<repo_name>"
    exit 1
fi

repo_name=$1

echo ""
echo ""
echo ""
echo "Clearing out old test files (but NOT full diff_test_output dirs)..."
echo ""
rm -fv $GEOIPS_TESTDATA_DIR/$repo_name/outputs/*diff_test_output* 2> /dev/null
rm -fv $GEOIPS_TESTDATA_DIR/$repo_name/outputs/*/*diff_test_output* 2> /dev/null
rm -fv $GEOIPS_PACKAGES_DIR/$repo_name/tests/outputs/*diff_test_output* 2> /dev/null
rm -fv $GEOIPS_PACKAGES_DIR/$repo_name/tests/outputs/*/*diff_test_output* 2> /dev/null
rm -fv $GEOIPS_PACKAGES_DIR/$repo_name/tests/outputs/*/*/*diff_test_output* 2> /dev/null
rm -fv $GEOIPS_PACKAGES_DIR/$repo_name/tests/outputs/*/*/*/*diff_test_output* 2> /dev/null
rm -fv $GEOIPS_PACKAGES_DIR/$repo_name/tests/outputs/*/*/*/*/*diff_test_output* 2> /dev/null

echo ""
echo ""
echo ""
echo "Copying the updated imagery files into $GEOIPS_TESTDATA_DIR/$repo_name/outputs/ ..."
echo ""
for fname in $GEOIPS_TESTDATA_DIR/$repo_name/outputs/*/diff_test_output*/cp_*; do source $fname; done
for fname in $GEOIPS_TESTDATA_DIR/$repo_name/outputs/*/*/diff_test_output*/cp_*; do source $fname; done
for fname in $GEOIPS_PACKAGES_DIR/$repo_name/tests/outputs/*/diff_test_output*/cp_*; do source $fname; done
for fname in $GEOIPS_PACKAGES_DIR/$repo_name/tests/outputs/*/*/diff_test_output*/cp_*; do source $fname; done
for fname in $GEOIPS_PACKAGES_DIR/$repo_name/tests/outputs/*/*/*/diff_test_output*/cp_*; do source $fname; done
for fname in $GEOIPS_PACKAGES_DIR/$repo_name/tests/outputs/*/*/*/*/diff_test_output*/cp_*; do source $fname; done

echo ""
echo ""
echo ""
echo "Running diffs on the newly copied files and the old files in the test repo:"
echo ""
# Look in both levels - some output product directories are directly in outputs, some in a subdirectory
for dirname in $GEOIPS_TESTDATA_DIR/$repo_name/outputs/* \
               $GEOIPS_TESTDATA_DIR/$repo_name/outputs/*/* \
               $GEOIPS_PACKAGES_DIR/$repo_name/tests/outputs/* \
               $GEOIPS_PACKAGES_DIR/$repo_name/tests/outputs/*/* \
               $GEOIPS_PACKAGES_DIR/$repo_name/tests/outputs/*/*/* \
               $GEOIPS_PACKAGES_DIR/$repo_name/tests/outputs/*/*/*/*; do
    for in_ext in jif png yaml; do

        # We want to write "jif" diffs out as "tif"
        out_ext=$in_ext
        if [[ $in_ext == "jif" ]]; then out_ext='png'; fi

        # We only want to diff files that do not already contain "diff_test_output"
        fnames=`ls -I diff_test_output $dirname/*.$in_ext 2> /dev/null`
        if [[ "$fnames" != "" ]]; then
            if [[ "$in_ext" == "yaml" ]]; then
                diff $fnames > ${dirname}_diff_test_output.yaml 2> /dev/null
            else
                compare -verbose -quiet -metric rmse -dissimilarity-threshold 0.000001 $fnames ${dirname}_diff_test_output.$out_ext 2> /dev/null
            fi
        fi
    done
done

echo ""
echo ""
echo ""
echo "Copying auto-generated diffs into $GEOIPS_TESTDATA_DIR/test_data_*/outputs/ "
echo ""
for dirname in $GEOIPS_TESTDATA_DIR/$repo_name/outputs/*/diff_test_output* \
               $GEOIPS_TESTDATA_DIR/$repo_name/outputs/*/*/diff_test_output* \
               $GEOIPS_PACKAGES_DIR/$repo_name/tests/outputs/*/diff_test_output* \
               $GEOIPS_PACKAGES_DIR/$repo_name/tests/outputs/*/*/diff_test_output* \
               $GEOIPS_PACKAGES_DIR/$repo_name/tests/outputs/*/*/*/diff_test_output* \
               $GEOIPS_PACKAGES_DIR/$repo_name/tests/outputs/*/*/*/*/diff_test_output*; do
    if [[ -d $dirname ]]; then
        # Automated diffs are named diff_test_output*
        # Post-generated diffs are named *diff_test_output
        cp -v $dirname/diff_test_output*.png $dirname/../../ 2> /dev/null
        cp -v $dirname/diff_test_output*.tif $dirname/../../ 2> /dev/null
        cp -v $dirname/diff_test_output*.yaml $dirname/../../ 2> /dev/null
    fi
done

echo ""
echo ""
echo ""
echo "Removing empty yaml diff files from $GEOIPS_TESTDATA_DIR/$repo_name/outputs"
echo ""
find $GEOIPS_TESTDATA_DIR/$repo_name/outputs -maxdepth 1 -type f -name '*yaml' -size 0 -exec rm -v {} \;

echo ""
echo ""
echo ""
echo "Now go look at the diffs in"
echo "    $GEOIPS_TESTDATA_DIR/$repo_name"
echo "    $GEOIPS_PACKAGES_DIR/$repo_name"
echo ""
echo "Once you have evaluated the diffs, run:"
echo "    $GEOIPS_PACKAGES_DIR/geoips/tests/utils/delete_files_from_repo.sh $repo_name"
echo "to finalize the test repo for update"
