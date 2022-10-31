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

Documentation and Style Strategy
===========================================

GeoIPS 2.0 uses Sphinx with the Napoleon extension for automated documentation generation.

https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html

The **geoips/docs** directory contains high level restructured text (rst) format documentation (including this page),
along with a **build_docs.sh** script that will setup sphinx and build complete documentation from the high level rst
files as well as docstrings contained within the GeoIPS 2.0 source code.


GeoIPS 2.0 Syntax and Style Checking
------------------------------------

GeoIPS 2.0 uses the NumPy docstring format within the code base for simplicity:

https://numpydoc.readthedocs.io/en/latest/format.html

bandit, flake8, and pylint are used to enforce appropriate style, security, and syntax usage.

The installation script called from **geoips/README.md** contains steps for setting up VIM8 with
automated syntax checking and highlighting (including automated flake8, pylint, and bandit error / warning
highlighting), to help enforce desired style guides.
