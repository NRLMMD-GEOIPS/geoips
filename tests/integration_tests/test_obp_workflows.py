# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Integration tests for order-based procflow (OBP) workflow YAML plugins.

Each test loads a workflow plugin, checks that test data is available, and
runs the workflow end-to-end using ``geoips test wf <workflow_name>``.  Tests are
marked as expected failures (``xfail``) when the requied test data is unavailable.
"""
