    # # # Distribution Statement A. Approved for public release. Distribution unlimited.
    # # #
    # # # Author:
    # # # Naval Research Laboratory, Marine Meteorology Division
    # # #
    # # # This program is free software: you can redistribute it and/or modify it under
    # # # the terms of the NRLMMD License included with this program. This program is
    # # # distributed WITHOUT ANY WARRANTY; without even the implied warranty of
    # # # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the included license
    # # # for more details. If you did not receive the license, for more information see:
    # # # https://github.com/U-S-NRL-Marine-Meteorology-Division/

Running test scripts
--------------------

Test scripts are explicitly specified commands that will return 0 if completely successful (including
comparisons of current outputs with "known" outputs - usually achieved by including the "--compare_path"
option to a run_procflow command).

To run a test script, just call the script.

Additionally, the "test_all.sh" script within each repository's "tests" directory contains calls
to ALL individual test scripts within that repository, to ensure we are tracking ALL required
functionality within each repository.

```
    # Run a single ABI static sector Infrared test case:
    $GEOIPS_PACKAGES_DIR/geoips/tests/scripts/abi.sh
    
    # Run multiple ABI products at once (TC Infrared-Gray, IR-BD, Visible, WV, and static Infrared)
    $GEOIPS_PACKAGES_DIR/geoips/tests/scripts/abi_config.sh
    
    # Test all modules for correct standard interface - this automatically tests any new modules,
    # no modifications required to this script.
    $GEOIPS_PACKAGES_DIR/geoips/tests/scripts/test_interface.py
    
    # Test ALL functionality within the current repo (just calls 3 scripts above, and ensures they all return 0)
    $GEOIPS_PACKAGES_DIR/geoips/tests/test_all.sh
```

Creating a new test repo
------------------------

Create a new test data repo for your data type, and populate it with data and appropriate sector information.
Create an empty "outputs" directory which you will later populate with valid test output, and a "tests" directory
for testing scripts.

If you would like to share your test_data repo with the community, please contact geoips@nrlmry.navy.mil
regarding linking it to the standard release (we do not want to include test data directly in the
geoips source repo for size considerations.)

```
mkdir -p $GEOIPS_TESTDATA_DIR/test_data_<type>
mkdir $GEOIPS_TESTDATA_DIR/test_data_<type>/data
mkdir $GEOIPS_TESTDATA_DIR/test_data_<type>/outputs
mkdir $GEOIPS_TESTDATA_DIR/test_data_<type>/sectors
mkdir -p $GEOIPS_TESTDATA_DIR/test_data_<type>/tests/scripts
vim $GEOIPS_TESTDATA_DIR/test_data_<type>/tests/test_all.sh
```

Create "test_all.sh" script which will contain calls to ALL test scripts required to completely
test all functionality.  Contents of test_all.sh as follows (replace items in <> appropriately):

```
   #!/bin/sh
   
   # This should contain test calls to cover ALL required functionality tests for the geoips repo.
   
   # The $GEOIPS tests modules sourced within this script handle:
   # setting up the appropriate associative arrays for tracking the overall return value,
   # calling the test scripts appropriately, and 
   # setting the final return value.
   
   # Note you must use the variable "call" in the for the loop
   
   . $GEOIPS_PACKAGES_DIR/geoips/tests/utils/test_all_pre.sh <repo_name>

   echo ""
   # "call" used in test_all_run.sh
   for call in \
               "$GEOIPS_TESTDATA_DIR/test_data_<type>/tests/scripts/<test_script_1>" \
               "$GEOIPS_TESTDATA_DIR/test_data_<type>/tests/scripts/<test_script_2>" \
               "$GEOIPS_TESTDATA_DIR/test_data_<type>/tests/scripts/<test_script_3>"
   do
       . $GEOIPS_PACKAGES_DIR/geoips/tests/utils/test_all_run.sh
   done

   . $GEOIPS_PACKAGES_DIR/geoips/tests/utils/test_all_post.sh
```

Creating a new test script
--------------------------

Ensure you have the appropriate versions of all dependencies for consistent test outputs!!
Ensure you are on the appropriate branch!!

```
$GEOIPS_PACKAGES_DIR/geoips/setup.sh install
$GEOIPS_PACKAGES_DIR/geoips/setup.sh install_cartopy_offlinedata
$GEOIPS_PACKAGES_DIR/geoips/setup.sh update_test_repo test_data_<type> <branch_name>
```

Test scripts must return 0 for a completely successful run, or nonzero for failure.

MUST COMPARE CURRENT IMAGERY/DATA OUTPUT PRODUCTS WITH "GOOD" OUTPUT PRODUCTS FOR 0 RETURN!

ALWAYS ADD NEW TEST SCRIPT TO test_all.sh !!

Log output from each test script MUST also contain one of the following strings upon successful completion
(happens automatically with "run_procflow" calls):

    * SUCCESSFUL COMPARISON DIR
    * GOODCOMPARE
    * FOUNDPRODUCT
    * SETUPSUCCESS
    * SUCCESSFUL INTERFACE

Log output from each test script may also contain one of the following strings for a piece of failed
fuctionality (happens automatically with "run_procflow --compare_path" calls):

    * BADCOMPARE
    * MISSINGCOMPARE
    * MISSINGPRODUCT
    * FAILED INTERFACE


Updating new test outputs
-------------------------

Once you've created a new test script, and produced valid test outputs, update the test repo and test_all.sh script:

```
   # Copy new files into test repos
   $GEOIPS_PACKAGES_DIR/geoips/tests/utils/copy_diffs_for_eval.sh <reponame>
   
   # Evaluate the new outputs, ensure everything looks good
   
   # Delete all the unnecessary files from the test repos, and any old "bad" products
   $GEOIPS_PACKAGES_DIR/geoips/tests/utils/delete_files_from_repo.sh <reponame>
   
   cd $GEOIPS_TESTDATA_DIR/test_data_<type>
   # git commit appropriately
   # git push
   
   # Add your new call to test_all.sh so we ensure it is in the testing rotation:
   vim $GEOIPS_PACKAGES_DIR/test_data/test_data_<type>/tests/test_all.sh
```
