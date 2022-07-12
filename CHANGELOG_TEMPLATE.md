#### # # Distribution Statement A. Approved for public release. Distribution unlimited.
#### # # 
#### # # Author:
#### # # Naval Research Laboratory, Marine Meteorology Division
#### # # 
#### # # This program is free software:
#### # # you can redistribute it and/or modify it under the terms
#### # # of the NRLMMD License included with this program.
#### # # 
#### # # If you did not receive the license, see
#### # # https://github.com/U-S-NRL-Marine-Meteorology-Division/
#### # # for more information.
#### # # 
#### # # This program is distributed WITHOUT ANY WARRANTY;
#### # # without even the implied warranty of MERCHANTABILITY
#### # # or FITNESS FOR A PARTICULAR PURPOSE.
#### # # See the included license for more details.

######################################################################################################################
DO NOT MODIFY THIS TEMPLATE!
FOR USE IN COMPILING CONSISTENT CHANGE LOGS!
######################################################################################################################

1. Follow below template when adding information to the CHANGELOG.md prior to opening a pull request
    * Distribution statement should already exist - no change required.
    * Do NOT add new title line (vX.Y.Z: YYYY-MM-DD), title line will be added during the version release process 
    * Follow proper formatting/categorization of changes below
        * newest changes go at the top, just below distribution statement.
        * Ensure sections are in correct order, as listed below
2. Only include headers for categories that have current updates (do NOT include empty headers)
3. "High level categories" are just to help sort and categorize updates - use your best judgment when determining
    categories.

```
<Appropriate Distribution Statement>


[ Version line NOT added until version update process, DO NOT include with individual updates ]
[ Included here for completeness ]
vX.Y.Z: YYYY-MM-DD, <short summary of change>

[ Issue IDs / pull request titles removed for final release ]
[ Included during pull request process for easy review during version update process ]
[     Issue ID like: GEOIPS/geoips#27 ]
[ Categorize each pull request's CHANGELOG updates separately - will be combined during version update ]

GEOIPS/<ISSUE_REPO>#<ISSUE_NUM> <reponame> <short description of updates>

### Breaking Interface Changes
* **<High level category - like "Readers" or "Products", etc>**
    * <List major BREAKING CHANGES>
        * <Additional optional information>

### Test Repo Updates
* **<High level category - like "AMSR2 Test Outputs" or "89H Products" or "Overlay Test Outputs", etc>**
    * <List major CHANGES THAT WILL IMPACT TEST REPOS (including changes to test repo output)>
        * <Additional optional information>

### Refactor
* **<High level category - like "Readers" or "Procflows", etc>**
    * <List major CHANGES TO CODE ORGANIZATION>
        * <Additional optional information>

### Major New Functionality
* **<High level category - like "Readers" or "Products", etc>**
    * <List MAJOR NEW FUNCTIONALITY>
        * <Additional optional information>

### Improvements
* **<High level category - like "Installation and Test" or "Test Comparisons" or "Readers", etc>**
    * <List major FEATURE IMPROVEMENTS>
        * <Additional optional information>

### Documentation Updates
* **<High level category - like "Installation" or "Test Comparisons" or "Readers" or "System Documentation", etc>**
    * <List major UPDATES TO DOCUMENTATION>
        * <Additional optional information>

### Installation and Test Scripts
* **<High level category - like "setup.sh" or "setup.py" or "setup_system.sh", etc>**
    * <List major UPDATES TO INSTALLATION OR TEST SCRIPTS>
        * <Additional optional information>

### Bug fixes
* **<High level category - like "Installation and Test" or "Test Comparisons" or "Readers", etc>**
    * <List major UPDATES TO DOCUMENTATION>
        * <Additional optional information>

### Performance Upgrades
* **<High level category - like "Readers" or "Procflows" or "Interpolation Routines", etc>**
    * <List major Performance Upgrades>
        * <Additional optional information>

GEOIPS/<ISSUE_REPO>#<ISSUE_NUM> <reponame> <short description of updates>

[ Use same CHANGELOG categories as above ]
```
