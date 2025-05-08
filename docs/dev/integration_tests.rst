.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _integration_tests:

Running Integration Tests
=========================

The GeoIPS integration tests leverage `pytest` to run a suite of scripts and
commands that verify the integrity and functionality of the installed GeoIPS and
GeoIPS plugins. These tests help ensure that installations are correct,
environment variables are properly set, and the system functions as expected.

Overview
========

This test suite runs a collection of integration test scripts located in
the `tests/scripts` directory of the GeoIPS repository and any associated
plugins. The scripts are executed via `pytest`, which manages test discovery,
execution, and reporting. The tests are separated into three broad categories:

- **Base integration tests**: A minimal set of tests that run quickly, ensuring
  that the basic GeoIPS installation and setup are correct.

- **Full integration tests**: A comprehensive set of tests that include
  building documentation, running plugin-specific tests, and verifying that
  all components function as intended. These may take a longer time to complete.

- **Extra integration tests**: A set of "extra" tests that implement functionality that
  require proprietary datasets or otherwise isn't ready for users.

Test Requirements
=================

Before running the integration tests, ensure that:

1. **GeoIPS is Installed Properly**:
   You must have a working GeoIPS installation with the `[test]` extra installed.

2. **Environment Variables**:
   The tests rely on various environment variables to locate GeoIPS components
   and plugins. The `setup_environment()` function automatically sets these
   variables. Make sure `GEOIPS_PACKAGES_DIR` is set before running the tests:

   .. code-block:: bash

       export GEOIPS_PACKAGES_DIR=/path/to/geoips_packages

Running the Tests
=================

To run the base integration tests (a minimal set of checks), execute:

.. code-block:: bash

    pytest -m "integration and base"

For the full suite of integration tests, which includes building documentation
and running plugin tests, execute:

.. code-block:: bash

    pytest -m "full and base"

If you want to run only the integration tests in the full set but not the base, run:

.. code-block:: bash

    pytest -m "integration and full"

For the "extra" suite of integration tests, which may require proprietary data sets,
execute:

.. code-block:: bash

    pytest -m "extra"


Running Tests in Parallel
=========================

To speed up test execution, particularly for the full test suite, you can use
`pytest-xdist` to run tests in parallel.
Simply add the `-n` option to specify the number of parallel workers:

- Specify a fixed number of workers (for example, 4):

  .. code-block:: bash

      pytest -m "full and integration" -n 4

- Or automatically detect the number of cores:

  .. code-block:: bash

      pytest -m "full and integration" -n auto

Using parallel execution can significantly reduce overall testing time,
especially if you have a multi-core machine and a large suite of tests.

Please be aware that running tests in parallel uses a large amount (>100Gb) of RAM.

Running a Single Parameterized Test Script
==========================================

Each individual script call is treated as
a separate test case. In some situations, you may need to run just one of
these tests to investigate or debug a particular issue.

Identifying the Test
====================

When executing tests, pytest generates a node ID for each parameterized test. This node ID uniquely
identifies the test function and the parameter instance.

To find the node ID associated with a specific script, first list out all
tests without running them:

.. code-block:: bash

    pytest -m integration --collect-only

This will print a list of all collected tests, including parameterized
instances. For example, you might see output like:

.. code-block:: text

    tests/test_integration.py::test_integ_full_test_script[script=$geoips_repopath/tests/scripts/amsr2.config_based_overlay_output.sh]

In this example, the full node ID for that particular test would be:

``tests/test_integration.py::test_integ_full_test_script[script=$geoips_repopath/tests/scripts/amsr2.config_based_overlay_output.sh]``

Running a Single Test
=======================

Once you have identified the specific test’s node ID, you can run just that
test by specifying the node ID directly:

.. code-block:: bash

    pytest
    tests/test_integration.py::test_integ_full_test_script[script=$geoips_repopath/tests/scripts/amsr2.config_based_overlay_output.sh]

This command executes only the selected parameterized test instance, allowing
you to focus on a single script without running the entire suite.

- **Using `-k` keyword expression**: If the parameter value (the script path)
  is unique, you could also try filtering tests by keyword. For example:

  .. code-block:: bash

      pytest -k "amsr2.config_based_overlay_output.sh"

  This would run any test whose node ID matches this expression. However,
  since multiple tests may contain similar substrings, this method is less
  precise than using the full node ID.

Interpreting Test Results
=========================

- **Successful Run**:
  If all tests pass, `pytest` will report a summary at the end indicating
  success (e.g, `== 53 passed in 30.00m ==`).

- **Failures**:
  If any script fails, `pytest` will display a traceback and the relevant
  command output. Since these scripts are run via bash, a `CalledProcessError`
  may be raised if the shell command returns a non-zero exit code. In such
  cases, review the error output to determine what went wrong, fix the
  underlying issue (or ask for help), and rerun the tests.

- **Debugging Failed Tests**:
  Consider running the failed script directly in a terminal to isolate the
  problem. For example, if a test script
  `"$geoips_repopath/tests/scripts/abi.config_based_output.sh"` fails, try
  running it separately:

  .. code-block:: bash

      cd $geoips_repopath
      bash tests/scripts/abi.config_based_output.sh

  This can help you identify environment issues, missing dependencies, or
  other runtime problems.
