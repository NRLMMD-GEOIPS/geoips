 | # # # Distribution Statement A. Approved for public release. Distribution unlimited.
 | # # #
 | # # # Author:
 | # # # Naval Research Laboratory, Marine Meteorology Division
 | # # #
 | # # # This program is free software: you can redistribute it and/or modify it under
 | # # # the terms of the NRLMMD License included with this program. This program is
 | # # # distributed WITHOUT ANY WARRANTY; without even the implied warranty of
 | # # # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the included license
 | # # # for more details. If you did not receive the license, for more information see:
 | # # # https://github.com/U-S-NRL-Marine-Meteorology-Division/

###################
GeoIPS git workflow
###################

Follow these steps when making modifications to geoips-based
packages or plugins

.. _create_issue:

***************************************
GeoIPS GitHub Issue Creation Workflow
***************************************

FROM WEB: Create an Issue for something that needs to be done
=============================================================

* Select an appropriate Issue template

  * Navigate to: https://github.com/NRLMMD-GEOIPS/geoips/issues

    * NOTE: you can create Issues on repos besides "geoips" if desired.
  * Click green “New Issue” button in top right
  * Click green "Get started" box to the right of the desired template
* Populate Issue contents appropriately

  * **Title**: Short descriptive name for the Issue
    (example: “Update GEOIPS_REPO_URL to GitHub”)
  * **Write**: Follow template within "Write" tab to populate
    with appropriate content
  * **Assignees**: Add Assignees as appropriate
  * **Labels**: Add descriptive labels as appropriate
  * **Projects**: Link to "GeoIPS - All Repos and all Functionality",
    other Projects as appropriate
* Click “Submit new issue”

.. _create_branch:

FROM WEB: MEMBERS: Create Branch from Existing Issue
===================================================================

**NOTE: Those who are NOT members of the GeoIPS organization will fork,**
**not branch. Skip to NON MEMBERS section**

* Navigate to Issue you would like to resolve
* Click on Development->Create Branch

  * **Branch name** Use auto-populated default branch name
  * **Repository Destination** Select repository to which you would like
    to make changes

    * NOTE you can create branches on repositories outside the repository
      the Issue resides in
  * **Change branch source** optional (defaults to "main")
  * Select **"Checkout locally"**
  * Click **"Create branch"**
  * Copy and paste the resulting "git fetch" and "git checkout" commands

FROM WEB: NON-MEMBERS: Create fork of repo
===================================================================
* **NOTE: NRLMMD-GEOIPS members will branch following steps above,
  **skip this section if you are a member**
* Navigate to desired repository
* Click drop down next to "Fork"
* Click "+ Create a new fork"
* Select appropriate owner/organization to own the fork
  (could be your individual github username)
* Uncheck "copy main branch only"
* Click "create fork"

******************************
GeoIPS command line workflow
******************************

FROM COMMAND LINE: Switch to new branch, Make changes as usual
===============================================================

* Navigate to repository of your choice

  * Issue only needs to be created on a single repository
  * You can create branches and make changes on any number of repos,
    as appropriate.
  * Related changes on different repositories will all be linked to
    the same Issue.

* Switch to new branch, and make changes as appropriate

  * *Ensure you copy and paste git fetch and git checkout commands*
    *when creating branch above*
  * Switch to new branch: Paste git fetch / git checkout commands
    specified when creating branch from Issue

    * git fetch origin
    * git checkout <new_branch_name>
  * <Make changes to code>
  * git commit # Frequently commit your changes

* Use enforced commit message format for all commits

  * Please follow
    `Commit Message Template <https://github.com/NRLMMD-GEOIPS/geoips/blob/main/COMMIT_MESSAGE_TEMPLATE.md>`_
  * Summary line <= 120 characters
  * Blank line (if commit message is more than one line)
  * OPTIONAL: additional details
  * Issue ID

* Update CHANGELOG.md in each repository with changes related to this Issue

  * Before pushing your final changes to GitHub and creating a pull request,
    you MUST update CHANGELOG.md appropriately
  * Please follow `CHANGELOG Template <https://github.com/NRLMMD-GEOIPS/geoips/blob/main/CHANGELOG_TEMPLATE.rst>`_
  * You will Copy and paste CHANGELOG modifications directly into the "Summary"
    section of pull request.
  * If CHANGELOG.md is not updated appropriately,
    pull request will be rejected.

* Create test scripts and associated outputs for any new functionality
    * Ensure any new functionality is tested in:
        * <repo>/tests/scripts/<test_name>.sh
    * Ensure new test scripts are included in:
        * <repo>/tests/test_all.sh


Push changes to github
=============================================================

* **From command line**: When you have made all of the changes required
  for the current Issue, push changes to GitHub

  * Perform once for each repository with changes related to this Issue
  * git push


.. _create_pull:

*************************************
GeoIPS GitHub Pull Request workflow
*************************************

FROM WEB: Create pull request from new ticket branch to "dev" branch
====================================================================

Follow these instructions for each repo that requires changes for a given
Issue.

* IF NEEDED: Navigate to Issue URL via web browser, and finalize with any
  last minute notes or resolutions

  * IF APPROPRIATE: Summary of overall changes
  * IF APPROPRIATE: Complete testing instructions
    (if multiple repostiories involved)
  * IF APPROPRIATE: Complete test output (if multiple repositories involved)
* Create a Pull Request on each repo with changes associated with the
  current Issue ID

  * Click on "Pull requests" tab within current repo
  * Click green “New pull request” button
  * **Source**: <new_branch_name>
  * **Destination**: main
  * Click green “Create pull request” button
* Fill Auto-populated template with appropriate content:

  * Generated from `Global Pull Request Template <https://github.com/NRLMMD-GEOIPS/.github/blob/main/.github/pull_request_template.md>`_
  * **Important to follow template title and contents directions**
    **for ease of review**
  * **Pull request will be denied if template is not followed appropriately**
* Ensure appropriate tags and attributes are set on the pull request

  * **Reviewers**: *Identify at least two Reviewers*
  * **Labels**: As appropriate
  * **Projects**: **VERY IMPORTANT**: *Select "GeoIPS - *
    *All Repos and All Functionality*, additional Projects if desired.
* Click “Create”

  * Now wait for the automated emails from GitHub saying your changes have been
    approved and merged.

.. _merge_pr_close:

******************************************
GeoIPS Merge PR and Close Issue workflow
******************************************

FROM WEB: Merge pull requests
=============================

This could include related pull requests from multiple repositories.

* Navigate to `GeoIPS Project <https://github.com/orgs/NRLMMD-GEOIPS/projects/1>`_
* Find current Issue card - Issue will have all associated PRs linked
* CTRL-Click on each linked pull request

  * Click green "Merge branch" from each PR
  * Click "Delete head branch" from each PR
* This should automatically update the Project so all related PRs and Issues
  are moved to the "Done" columnn

FROM WEB: Ensure all Issues and Pull Requests were successfully closed
======================================================================

* Could require approvals / merges from multiple pull requests in
  multiple repos before closing Issue
* Navigate to `GeoIPS Project <https://github.com/orgs/NRLMMD-GEOIPS/projects/1>`_
* Ensure all related Issue and Pull Request cards were automatically
  moved to the "Done" column

