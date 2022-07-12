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

#############################################################
GeoIPS git workflow, for updates to any geoips packages
#############################################################

Follow these steps when making modifications to geoips-based packages or plugins 

***************************************
GeoIPS GitHub Issue Creation Workflow
***************************************

FROM WEB: Create an Issue for something that needs to be done
=============================================================
* Select an appropriate Issue template
    * Navigate to: $GEOIPS_REPO_URL/geoips/issues
    * Click green “New Issue” button in top right 
    * Click green "Get started" box to the right of the desired template
    * Issue templates are generated from: $GEOIPS_REPO_URL/.github/tree/dev/.github/ISSUE_TEMPLATE
* Populate Issue contents appropriately
    * **Title**: Short descriptive name for the Issue (example: “Update GEOIPS_REPO_URL to GitHub”)
    * **Write**: Follow template within "Write" tab to populate with appropriate content
    * **Assignees**: Add Assignees as appropriate
    * **Projects**: Link to "GeoIPS - All Repos and all Functionality", other Projects as appropriate
* Click “Submit new issue”
    * In this example, Issue geoips#8 was created
* Add label with newly created Issue id
    * **Description**: Copy-paste "Title" from Issue
    * **Color**: #00FF00 (So all Issue id labels are bright green for easy identification)
    * **Label name**: geoips#<NN> (ie, geoips#8 in this example)



******************************
GeoIPS command line workflow
******************************

FROM COMMAND LINE: Switch to new branch, Make changes as usual
===============================================================
* Navigate to repository of your choice
    * Issue only needs to be created on a single repository
    * you can create "geoips#<issue_id>" branches and make changes on any number of repos, as appropriate (geoips#8 branch name in this example)
    * Related changes on different repositories will all reference the same Issue.

* Switch to branch named geoips#<issue_id>, and make changes as appropriate
    * *Branch named geoips#8 in this example - every repo will use the same branch name.*
    * git pull
    * git checkout <source_branch>  # Switch to whatever branch you want to branch from (typically dev)
    * git checkout -b <geoips#8> # Use your new issue id set above
    * git pull origin dev  # pull changes from dev to keep your branch updated as needed
    * git commit # Frequently commit your changes

* Use enforced commit message format for all commits
    * Please follow commit message template:
    * $GEOIPS_REPO_URL/geoips/blob/dev/COMMIT_MESSAGE_TEMPLATE.md
        * Summary line <= 120 characters
        * Blank line (if commit message is more than one line)
        * OPTIONAL: additional details
        * Issue ID

* Update CHANGELOG.md in each repository with changes related to this Issue
    * Before pushing your final changes to GitHub and creating a pull request, you MUST update CHANGELOG.md appropriately
    * Please follow CHANGELOG\_TEMPLATE.md:
    * $GEOIPS_REPO_URL/geoips/blob/dev/CHANGELOG_TEMPLATE.md
    * You will Copy and paste CHANGELOG modifications directly into the "Summary" section of pull request.
    * If CHANGELOG.md is not updated appropriately, pull request will be rejected.

Push changes to bitbucket 
=============================================================
* **From command line**: When you have made all of the changes required for the current Issue, push changes to GitHub
    * Perform once for each repository with changes related to this Issue
    * git push --set-upstream origin <geoips#8>  # Use your new branch name


*************************************
GeoIPS GitHub Pull Request workflow
*************************************

FROM WEB: Create pull request from new ticket branch to "dev" branch, on each associated repo
=============================================================================================
* IF NEEDED: Navigate to Issue URL via web browser, and finalize with any last minute notes or resolutions
    * IF APPROPRIATE: Summary of overall changes
    * IF APPROPRIATE: Complete testing instructions (if multiple repostiories involved)
    * IF APPROPRIATE: Complete test output (if multiple repositories involved)
* Create a Pull Request on each repo with changes associated with the current Issue ID
    * Click on "Pull requests" tab within current repo
    * Click green “New pull request” button
    * **Source**: geoips#<issue_num>  (this example is geoips#8 for all repos)
    * **Destination**: dev
    * Click green “Create pull request” button
* Fill Auto-populated template with appropriate content:
    * Generated from: $GEOIPS_REPO_URL/.github/blob/dev/.github/pull_request_template.md
    * **Important to follow template title and contents directions for ease of review**
    * **Pull request will be denied if template is not followed appropriately**
* Ensure appropriate tags and attributes are set on the pull request
    * **Reviewers**: *Identify at least two Reviewers*
    * **Labels**: **VERY IMPORTANT**: *Set label TO THE ISSUE ID (geoips#<issue_id>, in this example geoips#8 for all repos)*
    * **Projects**: **VERY IMPORTANT**: *Select "GeoIPS - All Repos and All Functionality*, additional Projects if desired.
* Click “Create”
    * Now wait for the automated emails from GitHub saying your changes have been approved and merged.


******************************************
GeoIPS Merge PR and Close Issue workflow
******************************************

* FROM WEB: Merge pull requests (could include related pull requests from multiple repositories)
    * Navigate to https://github.com/orgs/NRLMMD-GeoIPS/projects/4
    * Enter "is:pr label:geoips#<issue_num>" into "Filter Cards" query in top right ("is:pr label:geoips#8" in this example. NO SPACE AFTER COLON!!)
    * CTRL-Click on each resulting pull request
    * Click green "Merge branch" from each PR
    * Click "Delete head branch" from each PR

* FROM WEB: Close issue, once all functionality has been approved and merged from an issue
    * Could require approvals / merges from multiple pull requests in multiple repos before closing Issue
    * Navigate to https://github.com/orgs/NRLMMD-GeoIPS/projects/4
    * Enter "is:issue label:geoips#<issue_num>" into "Filter Cards" query in top right ("is:issue label:geoips#8" in this example. NO SPACE AFTER COLON!!)
    * CTRL-Click resulting Issue
    * Click "Close issue" 
    * Select "Done"
