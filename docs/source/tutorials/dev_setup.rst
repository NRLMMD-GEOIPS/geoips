.. dropdown:: Distribution Statement

 | # # # This source code is protected under the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

Setting up for development on core GeoIPS
*****************************************

Instructions for setting up a new data type
===========================================

Instructions for setting up a new data type, including:

* creating a new geoips test data repository from template,
* creating a new geoips plugin repository from template,

This example will use a data type called "mydatatype".

Anything denoted with an '@' symbol within these instructions and within
the associated templates will need to be modified accordingly, based on
your desired functionality

Follow Issue, Branch Pull Request Process if within GEOIPS org
--------------------------------------------------------------

This only required if you are creating a new repository within the NRLMMD GEOIPS
organization. If you are creating functionality within your own organization,
you can follow your own version control process.

1. Create branch for updates
    * Follow Issue, Branch, Pull Request process in $GEOIPS/docs/source/devguide/git_workflow.rst
    * `Git Workflow <./git_workflow.rst>`

Create test data repo
---------------------

If a new data type is required for your plugin, create a separate test data repo
to hold the test datasets. Source code and test outputs are stored separately from
test datasets (idea being test datasets are effectively static, and will very
infrequently require updates, unless new datasets are added).

Use the "template_test_data" template on github

* https://github.com/NRLMMD-GEOIPS/template_test_data
* Click green "Use this template" button top right
* Owner: GEOIPS

  * NOTE if you do not have permissions to create a repo,
    contact geoips@nrlmry.navy.mil,
    or create it under your own organization / user.
* Repository name: geoips_@mydatatype@
* Description: @Include useful description@
* Private: Select "Private"
* Include all branches: SELECT
* Click green "Create repository from template" button at bottom

* Repository name: geoips_@mydatatype@
* Description: @Include useful description@
* Private: Select "Private"
* Include all branches: SELECT
* Click green "Create repository from template" button at bottom

.. code:: bash

    cd $GEOIPS_TESTDATA_DIR     # By standard convention, place within
                                # $GEOIPS_TESTDATA_DIR/test_data_@mydatatype@ on the filesystem.
    git clone https://github.com/NRLMMD-GEOIPS/test_data_@mydatatype@

Follow instructions in template README

Create GeoIPS plugin repository for readers / products
------------------------------------------------------

Use the "template_basic_plugin" template on github

* https://github.com/NRLMMD-GEOIPS/template_basic_plugin
* Click green "Use this template" button top right
* Owner: GEOIPS

  * NOTE if you do not have permissions to create a repo,
    contact geoips@nrlmry.navy.mil,
    or create it under your own organization / user.
* Repository name: geoips_@mydatatype@
* Description: @Include useful description@
* Private: Select "Private"
* Include all branches: SELECT
* Click green "Create repository from template" button at bottom

.. code:: bash

    cd $GEOIPS_PACKAGES_DIR
    git clone https://github.com/NRLMMD-GEOIPS/geoips_@mydatatype@

Follow instructions in template README
