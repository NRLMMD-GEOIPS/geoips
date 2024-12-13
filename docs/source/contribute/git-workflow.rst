.. dropdown:: Distribution Statement

 | # # # This source code is protected under the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

GeoIPS git workflow
###################

Follow these steps when making modifications to geoips-based
packages or plugins

Contributions generally follow the process of:

1. Submit a GitHub Issue for a bug fix or feature request. :ref:`create_issue`
2. Branch off a given Issue in order to make the required changes :ref:`create_branch`
3. Create a github Pull Request in order for your changes to be reviewed
   prior to being merged to the integration branch :ref:`create_pull`
4. Ensure all required tests pass prior to PR approval (more info coming soon)

   * Unit tests
   * Integration tests
   * Code formatting/style tests
   * Documentation formatting/style tests

5. Merge your changes into the main code base! :ref:`merge_pr_close`

.. _create_issue:

GeoIPS GitHub Issue Creation Workflow
*************************************

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
====================================================

**NOTE: Those who are NOT members of the GeoIPS organization will fork,**
**not branch. If you are unable to branch, skip to NON MEMBERS section**

* Navigate to Issue you would like to resolve
* Click on Development->Create Branch

  * **Branch name** Use auto-populated default branch name
  * **Repository Destination** Select repository to which you would like
    to make changes

    * NOTE you can create branches on repositories outside the repository
      the Issue resides in
  * **Change branch source** optional (defaults to default branch)
  * Select **"Checkout locally"**
  * Click **"Create branch"**
  * Copy and paste the resulting "git fetch" and "git checkout" commands

FROM WEB: NON-MEMBERS: Create fork of repo
==========================================
* **NOTE: GeoIPS organization members will branch following steps above,
  **skip this section if you are a member and are able to branch**
* Navigate to desired repository
* Click drop down next to "Fork"
* Click "+ Create a new fork"
* Select appropriate owner/organization to own the fork
  (could be your individual github username)
* Uncheck "copy main branch only"
* Click "create fork"

GeoIPS command line workflow
****************************

FROM COMMAND LINE: Switch to new branch/fork, Make changes as usual
===================================================================

* Navigate to repository of your choice

  * Issue only needs to be created on a single repository
  * You can create branches/forks and make changes on any number of
    repos, as appropriate.
  * Related changes on different repositories will all be linked to
    the same Issue.

* Switch to new branch/fork, and make changes as appropriate

  * *Ensure you copy and paste git fetch and git checkout commands*
    *when creating branch/fork above*
  * Switch to new branch/fork: Paste git fetch / git checkout commands
    specified when creating branch from Issue

    * git fetch origin
    * git checkout <new_branch_name>
  * <Make changes to code>
  * git commit # Frequently commit your changes

* Use enforced commit message format for all commits

  * Please follow `Commit Message Template
    <https://github.com/NRLMMD-GEOIPS/geoips/blob/main/COMMIT_MESSAGE_TEMPLATE.md>`_
  * Summary line <= 120 characters
  * Blank line (if commit message is more than one line)
  * OPTIONAL: additional details
  * Issue ID

* Update release notes in each repository with changes related to this Issue

  * Before pushing your final changes to GitHub and creating a pull request,
    you MUST update the release notes with your current changes.
  * Instructions found in `CHANGELOG.rst
    <https://github.com/NRLMMD-GEOIPS/geoips/blob/main/CHANGELOG.rst>`_
  * If release notes are not updated properly, pull request will not be approved.

* Create test scripts and associated outputs for any new functionality
    * Ensure any new functionality is tested in:
        * <repo>/tests/scripts/<test_name>.sh
    * Ensure new test scripts are included in:
        * <repo>/tests/test_all.sh

Push changes to github
======================

* **From command line**: When you have made all of the changes required
  for the current Issue, push changes to GitHub

  * Perform once for each repository with changes related to this Issue
  * git push

.. _create_pull:

GeoIPS GitHub Pull Request workflow
***********************************

FROM WEB: Create pull request from new ticket branch to default branch
======================================================================

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

  * Generated from `Global Pull Request Template
    <https://github.com/NRLMMD-GEOIPS/.github/blob/main/.github/pull_request_template.md>`_
  * **Important to follow template title and contents directions**
    **for ease of review**
  * **Pull request will not be approved if template is not followed appropriately**
* Ensure appropriate tags and attributes are set on the pull request

  * **Reviewers**: *Identify at least two Reviewers*
  * **Labels**: As appropriate
  * **Projects**: **VERY IMPORTANT**: *Select "GeoIPS - *
    *All Repos and All Functionality*, additional Projects if desired.
* Click “Create”

  * Now wait for the automated emails from GitHub saying your changes have been
    approved and merged.

.. _pr_review:

GeoIPS GitHub Pull Request Review and Approval workflow
*******************************************************

FROM WEB: Wait for PR review and approval
=========================================

Once the PR is finalized, it will require review and approval by a GeoIPS organization
member with write privileges on the repository who is tagged as a reviewer on your PR.
Ensure you address/resolve any conversations or change requests made by the reviewers
during the review process.

Once all requests/conversations have been addressed, the PR will be approved and merged.

Reviewers can approve the PR by:

* clicking on the green "Review changes" button under the "Files changed" tab,
* selecting "Approve", then
* clicking the green "Submit review" button.

.. _merge_pr_close:

GeoIPS Merge PR and Close Issue workflow
****************************************

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
