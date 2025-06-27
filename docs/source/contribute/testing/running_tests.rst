Running GeoIPS Pytest Tests
=======================

Basic Usage
-----------

Run all tests (excluding limited dataset tests)::

    pytest

Run with verbose output::

    pytest -v

Run tests from a specific test file::

    pytest tests/unit_tests/test_example.py

Run specific test class::

    pytest tests/unit_tests/test_example.py::TestClassName

Run specific test function::

    pytest tests/unit_tests/test_example.py::test_function_name

Run specific method from test class::

    pytest tests/unit_tests/test_example.py::TestClassName::test_method_name

Long-Running Unit Tests
~~~~~~~~~~~~~~~~~~~~~~~

Run long-running unit tests (not included in default test paths)::

    pytest tests/unit_tests_long/

Combine long unit tests with regular tests::

    pytest tests/unit_tests/ tests/unit_tests_long/

Run long unit tests with specific markers::

    pytest tests/unit_tests_long/ -m "integration"

Marker Categories
-----------------

GeoIPS uses three categories of pytest markers:

**Concurrent Markers**: Can be applied with any other marker
  - ``integration``, ``spans_multiple_packages``, 
    ``limited_test_dataset_availability``

**Repository-Level Markers**: Mutually exclusive, test current repository functionality
  - ``base``, ``full``

**System Implementation Markers**: Mutually exclusive, test full GeoIPS system deployment
  - ``realtime``, ``scheduler``, ``database``, 
    ``downloader``, ``external_preprocessing``, ``scrubber``

For more information about what these markers mean,
see our testing markers documentation.

Marker-Based Test Selection
---------------------------

Repository-Level Markers
~~~~~~~~~~~~~~~~~~~~~~~~~

**Base Tests** - Quick tests for minimal installations::

    pytest -m "base"

Base tests complete very quickly and require only minimal 
installation for testing basic functionality within the current repository.

**Full Tests** - Comprehensive repository testing::

    pytest -m "full"

Full tests require complete installation and test only functionality within 
the current repository. These tests depend on ``geoips`` being installed.
This includes all repository tests except those 
marked as optional ``base`` tests.

Run both base and full tests::

    pytest -m "base or full"

Integration Test Markers
~~~~~~~~~~~~~~~~~~~~~~~~~

**Integration Tests** - Cross-component functionality::

    pytest -m "integration"

Integration tests verify functionality across multiple components and/or packages.

Exclude integration tests (unit tests only)::

    pytest -m "not integration"

**Multi-Package Tests** - Cross-repository dependencies::

    pytest -m "spans_multiple_packages"

This tests functionality that could fail due to code 
in multiple repositories (e.g., plugin validation across repos).

**Limited Dataset Tests** - Restricted data availability::

    pytest -m "limited_test_dataset_availability"

Run just tests that may not be available to all users 
due to dataset access restrictions or a lack of a 
pre-packaged opensource testing set.

GeoIPS System Implementation Markers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These markers test complete GeoIPS system deployments 
for real-time processing. 
Most GeoIPS developers will not use these markers.

**Real-time Tests** - End-to-end processing::

    pytest -m "realtime"

Tests full real-time functionality using complete 
procflow/workflow configs and all installed plugins.

**Scheduler Tests** - Task scheduling::

    pytest -m "scheduler"

Tests scheduling capabilities for processing workflows.

**Database Tests** - Database integration::

    pytest -m "database"

Tests database integrations.

**Downloader Tests** - Data ingestion::

    pytest -m "downloader"

Tests automated data download and ingestion functions.

**External Preprocessing Tests** - Third-party integration::

    pytest -m "external_preprocessing"

Tests/runs external preprocessing tools 
(e.g., CLAVR-x, CSPP) that are not part of core GeoIPS.

**Scrubber Tests** - Data cleanup::

    pytest -m "scrubber"

Tests data cleanup and maintenance functions.

Combined Marker Examples
~~~~~~~~~~~~~~~~~~~~~~~~

Run base integration tests::

    pytest -m "base and integration"

Run full tests excluding those requiring external datasets::

    pytest -m "full and not limited_test_dataset_availability"

Run all system implementation tests::

    pytest -m "realtime or scheduler or database or downloader or external_preprocessing or scrubber"

Run integration tests that don't span multiple packages::

    pytest -m "integration and not spans_multiple_packages"

Pattern Matching Examples
--------------------------

**Test Name Patterns**

Run tests containing "reader" in the name::

    pytest -k "reader"

Run tests for specific functionality::

    pytest -k "test_colormap"

Run tests NOT containing specific words::

    pytest -k "not slow"

Combine multiple patterns with AND::

    pytest -k "reader and viirs"

Combine multiple patterns with OR::

    pytest -k "reader or writer"

Complex pattern combinations::

    pytest -k "(reader or writer) and not slow"

**File Pattern Examples**

Run all reader tests::

    pytest -k "test_*_reader"

Run all tests ending with "integration"::

    pytest -k "*integration"

Run tests matching class patterns::

    pytest -k "TestReader or TestWriter"

Coverage and Output Options
---------------------------

**Coverage Reports**

Generate HTML coverage report::

    pytest --cov-report=html

Generate XML coverage report::

    pytest --cov-report=xml

Generate coverage report to terminal::

    pytest --cov-report=term

Show missing lines in terminal coverage::

    pytest --cov-report=term-missing

Generate annotated source code coverage::

    pytest --cov-report=annotate

Combine multiple coverage formats::

    pytest --cov-report=html --cov-report=term-missing

Specify coverage source directory::

    pytest --cov=geoips --cov-report=html

Set coverage output directory::

    pytest --cov-report=html:htmlcov

Exclude files from coverage::

    pytest --cov=geoips --cov-report=html --cov-config=.coveragerc

Show coverage for specific modules only::

    pytest --cov=geoips.interfaces --cov-report=term-missing

Fail if coverage below threshold::

    pytest --cov=geoips --cov-fail-under=80

**Test Execution Control**

Stop on first failure::

    pytest -x

Stop after N failures::

    pytest --maxfail=3

Run failed tests first::

    pytest --ff

Run last failed tests only::

    pytest --lf

Run new tests first::

    pytest --nf

**Output Formatting**

Show only failures and errors::

    pytest -rf

Show extra test summary (all except passed)::

    pytest -ra

Show all test outcomes::

    pytest -rA

Show skipped tests::

    pytest -rs

Show expected failures::

    pytest -rx

Quiet output (reduce verbosity)::

    pytest -q

Extra verbose output::

    pytest -vv

Show local variables in tracebacks::

    pytest -l

Capture output (show print statements)::

    pytest -s

Disable output capturing completely::

    pytest --capture=no

**Traceback Options**

Short traceback format::

    pytest --tb=short

Long traceback format (default)::

    pytest --tb=long

No traceback::

    pytest --tb=no

Only show one line per failure::

    pytest --tb=line

Native Python traceback::

    pytest --tb=native

**Progress and Timing**

Show slowest test durations::

    pytest --durations=10

Show all test durations::

    pytest --durations=0

Show test progress as percentage::

    pytest --tb=no -q --durations=0

Disable duration reporting::

    pytest --durations=0

**Warning Control**

Disable warnings::

    pytest --disable-warnings

Show warnings summary::

    pytest -rw

Turn warnings into errors::

    pytest -W error

Filter specific warnings::

    pytest -W ignore::DeprecationWarning

Managing Pytest Output and Logging
---------------------------------------------

Pytest can generate substantial output, especially when running comprehensive test suites with verbose logging.
This section covers techniques for capturing, redirecting, and managing pytest output effectively.

**Redirecting Output to Files**

Capture all pytest output to a file::

    pytest > test_results.txt 2>&1

Separate stdout and stderr::

    pytest > test_output.txt 2> test_errors.txt

Append to existing log files::

    pytest >> test_log.txt 2>&1

Capture only test results (suppress pytest's own output)::

    pytest -q > results.txt 2>&1

Create timestamped log files::

    pytest > "test_$(date +%Y%m%d_%H%M%S).log" 2>&1

Control pytest verbosity levels::

    pytest -v > verbose_output.txt          # Standard verbose
    pytest -vv > extra_verbose_output.txt   # Extra verbose
    pytest -q > quiet_output.txt            # Minimal output

Filter output by test outcomes::

    pytest -ra > all_summary.txt            # All test summary info
    pytest -rf > failures_only.txt          # Only failures and errors
    pytest -rs > skipped_tests.txt          # Only skipped tests

Enable live logging to see real-time output::

    pytest --log-cli-level=INFO > test_with_logs.txt 2>&1

Capture logs at different levels::

    pytest --log-level=DEBUG > debug_logs.txt 2>&1
    pytest --log-level=WARNING > warning_logs.txt 2>&1

Configure log format for file output::

    pytest --log-cli-format="%(asctime)s [%(levelname)s] %(message)s" > formatted_logs.txt 2>&1

Use progress indicators for long-running tests::

    pytest --tb=line -q | tee progress.log

Rotate logs by test session::

    pytest > "session_$(date +%s).log" 2>&1

Split output by test categories::

    pytest -m "base" > base_tests.log 2>&1
    pytest -m "integration" > integration_tests.log 2>&1

**Output Size Management**

Limit traceback length to reduce file size::

    pytest --tb=short > compact_results.txt 2>&1
    pytest --tb=no > minimal_results.txt 2>&1

Compress output files automatically::

    pytest 2>&1 | gzip > test_results.gz

**Real-time Monitoring**

Monitor test progress in real-time::

    pytest | tee test_output.txt

Follow log files during test execution::

    pytest > test.log 2>&1 &
    tail -f test.log

Run multiple test configurations with separate logs::

    pytest -m "base" > base.log 2>&1
    pytest -m "integration" > integration.log 2>&1
    pytest -m "full" > full.log 2>&1

Multi-Package Coverage Example
------------------------------

Run tests across all GeoIPS plugin packages with comprehensive coverage::

    cd $GEOIPS_PACKAGES_DIR
    coverage run --omit=*test* --source ./.. --module \
          pytest -m '$pytest_mark' \
          --junit-xml=/output/test-artifacts/pytest.xml \
          --html=/output/test-artifacts/pytest.html --self-contained-html
    coverage json -o /output/test-artifacts/coverage.json --pretty-print
    coverage lcov -o /output/test-artifacts/coverage.lcov
    coverage html -d /output/test-artifacts/coverage-html

This example:
  - Uses ``coverage run`` to collect coverage data across all packages
  - Omits test files from coverage analysis with ``--omit=*test*``
  - Sets source directory to parent directory with ``--source ./..``
  - Runs pytest as a module with specified markers
  - Generates JUnit XML for CI/CD integration
  - Creates self-contained HTML test report
  - Exports coverage in multiple formats (JSON, LCOV, HTML)

Advanced Usage
--------------

**Parallel Execution**

Run tests in parallel (requires pytest-xdist)::

    pytest -n auto

Specify number of parallel workers::

    pytest -n 4

Distribute tests across multiple CPUs::

    pytest -n logical

**Complex Examples**

Run with custom markers and options::

    pytest -m "integration and not limited_test_dataset_availability" --cov-report=html -v

Exclude specific directories::

    pytest --ignore=tests/integration_tests/

Include long unit tests with coverage::

    pytest tests/unit_tests/ tests/unit_tests_long/ --cov-report=html

Pattern matching with coverage::

    pytest -k "reader" --cov=geoips.interfaces.readers --cov-report=term-missing

**Development and Debugging**

Dry run (collect tests without running)::

    pytest --collect-only

Debug mode (drop into debugger on failures)::

    pytest --pdb

Drop into debugger on first failure::

    pytest -x --pdb

Set trace immediately::

    pytest --trace

**CI/CD Integration**

Create JUnit XML output for CI/CD::

    pytest --junit-xml=results.xml

Create JSON report::

    pytest --json-report --json-report-file=report.json

Combine XML and coverage for CI::

    pytest --junit-xml=results.xml --cov-report=xml --cov-report=term

**Performance Testing**

Run with benchmark plugin (if installed)::

    pytest --benchmark-only

Profile test execution::

    pytest --profile

Memory usage profiling::

    pytest --memray

Extended Pytest Functionality
------------------------------

**Core Extensions**
  - `pytest-cov <https://pytest-cov.readthedocs.io/>`_ - Coverage reporting
  - `pytest-xdist <https://pytest-xdist.readthedocs.io/>`_ - Parallel test execution
  - `pytest-html <https://pytest-html.readthedocs.io/>`_ - HTML test reports

**Development Tools**
  - `pytest-mock <https://pytest-mock.readthedocs.io/>`_ - Enhanced mocking capabilities
  - `pytest-benchmark <https://pytest-benchmark.readthedocs.io/>`_ - Performance benchmarking
  - `pytest-memray <https://pytest-memray.readthedocs.io/>`_ - Memory profiling

**CI/CD Integration**
  - `pytest-json-report <https://pytest-json-report.readthedocs.io/>`_ - JSON test reports
  - `pytest-timeout <https://pytest-timeout.readthedocs.io/>`_ - Test timeout handling
  - `pytest-rerunfailures <https://pytest-rerunfailures.readthedocs.io/>`_ - Retry failed tests

**Quality Assurance**
  - `pytest-flake8 <https://pypi.org/project/pytest-flake8/>`_ - Code style checking
  - `pytest-mypy <https://pypi.org/project/pytest-mypy/>`_ - Type checking integration
  - `pytest-clarity <https://pytest-clarity.readthedocs.io/>`_ - Better assertion output
