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

::

   ####################################################################################
   DO NOT MODIFY THIS TEMPLATE!
   FOR USE IN COMPILING CONSISTENT CHANGE LOGS / RELEASE NOTES!

   NOTE: RST IS VERY PARTICULAR ABOUT SPACING / INDENTATIONS!
   FOLLOW THIS TEMPLATE CLOSELY TO ENSURE PROPER RENDERING (and read up on rst syntax)
   ####################################################################################

1. Follow below template when adding information to the CHANGELOG.rst
   prior to opening a pull request

   -  Follow proper formatting/categorization of changes below

      -  newest changes go at the top, just below distribution
         statement.
      -  Ensure sections are in correct order, as listed below
      -  Follow spacing and indentation in template closely,
         RST is very particular about spacing and indentation
         (and read up on RST syntax for good measure).

   -  If you make changes during the Pull Request process, just update
      the CHANGELOG entry accordingly, do not add an additional
      CHANGELOG entry. We only want the information regarding the final
      merged pull request in the CHANGELOG.

2. Only include headers for categories that have current updates (do NOT
   include empty headers - if there are no "Breaking Changes" do not include the
   "Breaking Changes" header)

3. Include a list of files for each "Summary of change" section.

   -  Simple changes can just have the list of modified files directly
      under the “Summary of change” section, without additional details.

4. Issue ID should match related linked issue, like: NRLMMD-GEOIPS/geoips#27
5. Note the contents of CHANGELOG.rst will be moved to
   docs/source/releases/vX_Y_Z.rst  during the PR review process. If you
   are feeling adventurous, you can add your entries directly there.

   - NOTE: X.Y.Z is the UPCOMING VERSION of the repository, NOT the current
     tagged version!


::

    ###################################################################################
    NOTE: RST IS VERY PARTICULAR ABOUT SPACING / INDENTATIONS!
    FOLLOW THIS TEMPLATE CLOSELY TO ENSURE PROPER RENDERING (and read up on rst syntax)
    ###################################################################################


Version X.Y.Z (YYYY-MM-DD)
**************************

* Very brief bulleted summary of changes
* Should reference major changes outlined below

Breaking Changes
================

<Short summary of breaking change 1 from this PR>
-------------------------------------------------

*From NRLMMD-GEOIPS/geoips#NN: YYYY-MM-DD, <short summary of all changes in this PR>*

* More info about the change

  * Additional optional information

::

    modified: /path/to/changed/file/related/to/breaking/change/1
    new: /path/to/new/file/related/to/breaking/change/1
    deleted: /path/to/deleted/file/related/to/breaking/change/1
    renamed: /path/to/orig/file -> /path/to/new/file

<Short summary of breaking change 2 from this PR>
-------------------------------------------------

*From NRLMMD-GEOIPS/geoips#NN: YYYY-MM-DD, <short summary of all changes in this PR>*

* More info about breaking Change 2

  * Additional optional information

* More info about breaking change 2

::

    modified: /path/to/changed/file1/related/to/breaking/change/2
    modified: /path/to/changed/file2/related/to/breaking/change/2

Security Updates
================

<Short summary of a security related change from this PR>
---------------------------------------------------------

*From NRLMMD-GEOIPS/geoips#NN: YYYY-MM-DD, <short summary of all changes in this PR>*

* required security change due to file update

::

    modified: /paths/to/changed/file(s)


Major New Functionality
=======================

<Short summary of new functionality from this PR>
-------------------------------------------------

*From NRLMMD-GEOIPS/geoips#NN: YYYY-MM-DD, <short summary of all changes in this PR>*

* Details about change related to new functionality

::

    modified: /paths/to/changed/file(s)


Enhancements
============

<Short summary of one enhancement from this PR>
-----------------------------------------------

*From NRLMMD-GEOIPS/geoips#NN: YYYY-MM-DD, <short summary of all changes in this PR>*

* Details about change related to improvements or enhancements to the code

::

    modified: /paths/to/changed/file(s)


Deprecations
============

<Short summary of a deprecation related change from this PR>
------------------------------------------------------------

*From NRLMMD-GEOIPS/geoips#NN: YYYY-MM-DD, <short summary of all changes in this PR>*

* Details about change related to code that has been or will be deprecated

::

    modified: /paths/to/changed/file(s)


Regression Fixes
================

<Short summary of a regression related change from this PR>
-----------------------------------------------------------

*From NRLMMD-GEOIPS/geoips#NN: YYYY-MM-DD, <short summary of all changes in this PR>*

* Details about change related to code that used to work in a previous release,
  and is now broken.

::

    modified: /paths/to/changed/file(s)


Bug Fixes
=========

<Short summary of a bug fix from this PR>
-----------------------------------------

*From NRLMMD-GEOIPS/geoips#NN: YYYY-MM-DD, <short summary of all changes in this PR>*

* Details about change related to bug fixes

::

    modified: /paths/to/changed/file(s)


Efficiency Improvements
=======================

<Short summary of an efficiency related change from this PR>
------------------------------------------------------------

*From NRLMMD-GEOIPS/geoips#NN: YYYY-MM-DD, <short summary of all changes in this PR>*

* Details about change related to efficiency improvements

::

    modified: /paths/to/changed/file(s)


Installation Updates
====================

<Short summary of an installation related change from this PR>
--------------------------------------------------------------

*From NRLMMD-GEOIPS/geoips#NN: YYYY-MM-DD, <short summary of all changes in this PR>*

* Details about change related to installation updates

::

    modified: /paths/to/changed/file(s)


Real-time Processing Updates
============================

<Short summary of a real time processing related change from this PR>
---------------------------------------------------------------------

*From NRLMMD-GEOIPS/geoips#NN: YYYY-MM-DD, <short summary of all changes in this PR>*

* Details about change related to real-time processing updates

::

    modified: /paths/to/changed/file(s)


Refactoring Updates
===================

<Short summary of a refactoring related change from this PR>
------------------------------------------------------------

*From NRLMMD-GEOIPS/geoips#NN: YYYY-MM-DD, <short summary of all changes in this PR>*

* Details about change related to code refactoring

::

    modified: /paths/to/changed/file(s)


Code Formatting and Style Updates
=================================

<Short summary of a formatting related change from this PR>
-----------------------------------------------------------

*From NRLMMD-GEOIPS/geoips#NN: YYYY-MM-DD, <short summary of all changes in this PR>*

* Details about change related to code formatting and style updates

::

    modified: /paths/to/changed/file(s)


GitHub Actions Updates
======================

<Short summary of a github actions related change from this PR>
---------------------------------------------------------------

*From NRLMMD-GEOIPS/geoips#NN: YYYY-MM-DD, <short summary of all changes in this PR>*

* Details about change related to GitHub Actions updates

::

    modified: /paths/to/changed/file(s)


Git Workflow Improvements
=========================

<Short summary of a git workflow related change from this PR>
-------------------------------------------------------------

*From NRLMMD-GEOIPS/geoips#NN: YYYY-MM-DD, <short summary of all changes in this PR>*

* Details about change related to Git workflow improvements

::

    modified: /paths/to/changed/file(s)

Test Repo Updates
=================

<Short summary of a testing related change from this PR>
--------------------------------------------------------

*From NRLMMD-GEOIPS/geoips#NN: YYYY-MM-DD, <short summary of all changes in this PR>*

* Details about change to TEST REPO OUTPUT

::

    modified: /paths/to/changed/file(s)

Testing Updates
===============

<Short summary of a testing related change from this PR>
--------------------------------------------------------

*From NRLMMD-GEOIPS/geoips#NN: YYYY-MM-DD, <short summary of all changes in this PR>*

* Details about change that WILL IMPACT TESTING
  (or change to testing process)

::

    modified: /paths/to/changed/file(s)


Documentation Updates
=====================

<Short summary of a documentation related change from this PR>
--------------------------------------------------------------

*From NRLMMD-GEOIPS/geoips#NN: YYYY-MM-DD, <short summary of all changes in this PR>*

* Details about change to documentation (contents, or build process)

::

    modified: /paths/to/changed/file(s)

