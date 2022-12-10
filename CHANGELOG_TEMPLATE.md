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

    ####################################################################################
    DO NOT MODIFY THIS TEMPLATE!
    FOR USE IN COMPILING CONSISTENT CHANGE LOGS!
    ####################################################################################

1. Follow below template when adding information to the CHANGELOG.md prior to opening a pull request
    * Distribution statement should already exist - no change required.
    * ONLY add new title line (vX.Y.Z: YYYY-MM-DD), title line if you are completing a version release process
    * Follow proper formatting/categorization of changes below
        * newest changes go at the top, just below distribution statement.
        * Ensure sections are in correct order, as listed below
        * One blank line between PR CHANGELOG entries
        * No blank line between individual sections within each PR CHANGELOG entry
        * Two blank lines between version CHANGELOG entries.
    * If you make changes during the Pull Request process, just update the CHANGELOG entry accordingly, do not add
      an additional CHANGELOG entry.  We only want the information regarding the final merged pull request in the
      CHANGELOG.
    * If modifications are required during a **Version Release** process, add a new CHANGELOG entry using the branch name for the Version Release.
2. Only include headers for categories that have current updates (do NOT include empty headers)
3. "High level categories" are just to help sort and categorize updates - use your best judgment when determining
    categories.  
     * Simple changes can just have the list of file updates directly under the "Headers" (Breaking Interface Changes, Test Repo Updates, etc)

```
<Appropriate Distribution Statement>


<!--- Version line NOT added until version update process, DO NOT include with individual updates --->
<!--- Included here for completeness --->
# vX.Y.Z: YYYY-MM-DD, <short summary of change>

<!--- Categorize each pull request's CHANGELOG updates separately --->
<!--- Only include one section per Pull Request - 
      update the contents of the CHANGELOG entry if updates are required during the PR process,
      do not add an additional section to the CHANGELOG entry.
      One CHANGELOG entry per merged Pull Request
--->
<!--- Issue ID should match related linked issue, like: GEOIPS/geoips#27 --->

## GEOIPS/geoips#NN: YYYY-MM-DD, <short description of updates>
### Breaking Interface Changes
#### <OPTIONAL High level category - like "Readers" or "Products", etc>
* **<filename>**: <breaking changes due to file update>
    * <Additional optional information>
### Test Repo Updates
#### <OPTIONAL High level category - like "AMSR2 Test Outputs" or "89H Products" or "Overlay Test Outputs", etc>
* **<filename>**: <change to file that WILL IMPACT TEST REPOS (including changes to test repo output)>
    * <Additional optional information>
### Refactor
#### <OPTIONAL High level category - like "Readers" or "Procflows", etc>
* **<filename>**: <describe each file's organizational changes>
    * <Additional optional information>
### Major New Functionality
#### <OPTIONAL High level category - like "Readers" or "Products", etc>
* **<filename>**: <describe each updated file's MAJOR NEW FUNCTIONALITY>
    * <Additional optional information>
### Real-time Processing Updates
#### <OPTIONAL High level category - like "Procflow Configs" or "Scripts", etc>
* **<filename>**: <describe each updated file's REAL-TIME PROCESSING UPDATE>
    * <Additional optional information>
### Real-time Testing
#### <OPTIONAL High level category - like "Procflow Configs" or "Test Scripts", etc>
* **<filename>**: <describe each updated file's REAL-TIME PROCESSING UPDATE>
    * <Additional optional information>
### Improvements
#### <OPTIONAL High level category - like "Installation and Test" or "Test Comparisons" or "Readers", etc>
* **<filename>**: <describe each file containing major FEATURE IMPROVEMENTS>
    * <Additional optional information>
### Documentation Updates
#### <OPTIONAL High level category - like "Installation" or "Test Comparisons" or "Readers" or "System Documentation", etc>
* **<filename>**: <describe each file containing major UPDATES TO DOCUMENTATION>
    * <Additional optional information>
### Installation and Test
#### <OPTIONAL High level category - like "setup.sh" or "setup.py" or "setup_system.sh", etc>
* **<filename>**: <describe each file containing major UPDATES TO INSTALLATION OR TEST SCRIPTS>
    * <Additional optional information>
### Bug fixes
#### <OPTIONAL High level category - like "Installation and Test" or "Test Comparisons" or "Readers", etc>
* **<filename>**: <describe each file containing bug fixes>
    * <Additional optional information>
### Performance Upgrades
#### <OPTIONAL High level category - like "Readers" or "Procflows" or "Interpolation Routines", etc>
* **<filename>**: <describe each file containing major Performance Upgrades>
    * <Additional optional information>

```
