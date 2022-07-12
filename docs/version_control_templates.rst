 | # # # Distribution Statement A. Approved for public release. Distribution unlimited.
 | # # # 
 | # # # Author:
 | # # # Naval Research Laboratory, Marine Meteorology Division
 | # # # 
 | # # # This program is free software:
 | # # # you can redistribute it and/or modify it under the terms
 | # # # of the NRLMMD License included with this program.
 | # # # 
 | # # # If you did not receive the license, see
 | # # # https://github.com/U-S-NRL-Marine-Meteorology-Division/
 | # # # for more information.
 | # # # 
 | # # # This program is distributed WITHOUT ANY WARRANTY;
 | # # # without even the implied warranty of MERCHANTABILITY
 | # # # or FITNESS FOR A PARTICULAR PURPOSE.
 | # # # See the included license for more details.

Pull Request Template
=====================

.. code-block:: bash
    [ Title should follow template of <ticket name> <repo name> <short description> ]
    [ This allows quickly looking through list of pull requests from either ticket or repo,
    [ and knowing exactly what each pertains to ]

    Title: GEOIPS-<XXX> <reponame> <Short description>

    [ The following information should be included in each Pull Request. ]
    [ Include information specific to the current repo within the pull request. ]
    [ Main testing and installation instructions will be included within the ticket, ]
    [ so the pull request should just include information about what changed within the current repo. ]
    
    # Testing Instructions
    GEOIPS-XX 
    <Link to ticket with testing instructions>
    <OR>
    <note that no exhaustive testing is required (if you have sufficient output below to demonstrate success>
    <OR>
    <include testing instructions directly here if appropriate>
    
    # Summary
    <COPY AND PASTE your CHANGELOG update here as summary bullet points>
    <NOTE Pull request WILL NOT be approved without appropriate updates added to the CHANGELOG>
        <CHANGELOG updates should come before the most recent version header>
        <a new version header will be added during the next version release cycle>
        < Please see geoips/CHANGELOG_TEMPLATE.md for appropriate CHANGELOG update formatting >

    # Output
    <Optional output demonstrating functionality - command line or imagery output>
    < If there is anything you can copy/paste here to indicate the changes you made work as expected, please include >
    
    # Individual Commits
    <Leave the auto-populated commit messages at the bottom of the pull request text.>


Ticket Resolution Template
==========================

.. code-block:: bash
    [ The following information should be included as a comment on the ticket once all repos are ready for approval/merge ]
    [ There may be more than one related repo - they should all be approved / merged as a group ]
    [ Once all ticket requirements are met, update the ticket with the following information ]
    [ Then all associated pull requests can be approved and merged ]
    
    This functionality is ready for review and approval - all tests successfully returned 0.
    
    ### Associated pull requests that should be merged with this approval are linked to ticket
    Navigate to each associated pull request, review changes, and approve individually.
    None will be merged until ALL are approved.
    
    ### Summary
    <2-3 sentence summary of the changes that were made to meet the requirements of the ticket>
    
    ### Instructions to set up required packages from scratch
    * [ https://<url>/repos/<package1>/browse/README.md ]
    * [ https://<url>/repos/<package2>/browse/README.md ]
    * [ https://<url>/repos/<package3>/browse/README.md ]
    
    
    ### Obtain the correct branch and reinstall all associated repos:
    ```
    $GEOIPS_PACKAGES_DIR/geoips/setup.sh update_source_repo <package1> feature/[GEOIPS-XX-DESCRIPTION]
    $GEOIPS_PACKAGES_DIR/geoips/setup.sh update_source_repo <package2> feature/[GEOIPS-XX-DESCRIPTION]
    $GEOIPS_PACKAGES_DIR/geoips/setup.sh update_source_repo <package3> feature/[GEOIPS-XX-DESCRIPTION]
    
    $GEOIPS_PACKAGES_DIR/geoips/setup.sh update_test_repo <testrepo1> feature/[GEOIPS-XX-DESCRIPTION]
    $GEOIPS_PACKAGES_DIR/geoips/setup.sh update_test_repo <testrepo2> feature/[GEOIPS-XX-DESCRIPTION]
        
    $GEOIPS_BASEDIR/geoips_packages/<package1>/setup_<package1>.sh install_<package1>
    $GEOIPS_BASEDIR/geoips_packages/<package2>/setup_<package2>.sh install_<package2>
    ```
      
    ### Obtain correct versions of all dependencies for consistent test outputs
    ```
    $GEOIPS/setup.sh install
    $GEOIPS/setup.sh install_cartopy_offlinedata
    ```
      
    
    ### Test the new functionality
    ```
    $GEOIPS_BASEDIR/geoips_packages/<package1>/tests/test_all.sh
    $GEOIPS_BASEDIR/geoips_packages/<package2>/tests/scripts/<script>.sh
    [ Include output indicating 0 returns ]
    ```
