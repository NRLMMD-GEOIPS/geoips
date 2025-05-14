.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

Where to Put Documentation
**************************

Flowchart
---------

Please use this flowchart to figure out where to put new documentation.

.. mermaid:: where-to-put-flowchart.mmd
    :zoom:

Guidelines
----------

- **Modifying Documentation Build**:
  If you're changing how the documentation is built:
  - Modify files in the ``_templates`` directory.
  - For Sphinx configuration, edit ``sphinx_conf.template.py``.
  - The homepage template is also located in ``_templates``.

- **Modifying Static Files or Styling**:
  If you're changing render files or styles:
  - Modify files in the ``_static`` directory.

- **Adding Release Notes**:
  - Add new release notes to ``releases/latest``.
  - During the release process, move ``latest`` to a versioned directory and create a new, empty ``latest`` directory.

- **Documenting Code**:
  - Document functions, methods, or files directly in the code using docstrings, which are integrated into the GeoIPS
    API.
  - If more detailed documentation is needed, also write an RST file in the appropriate section.

- **Contributing to the Project**:
  - Information about contributing (but not using) goes into the ``contribute`` folder.

- **Step-by-Step Tutorials**:
  - Add tutorials or any step-by-step instructions to the ``tutorials`` folder.

- **Conceptual Information**:
  - **How the Code Works or Is Organized**: Place this information in the ``concepts`` directory.
  - **Usage Information**: Instructions on how to use or operate something go into ``concepts/functionality``.
  - **Architecture Details**: Information on how GeoIPS works internally or why it's structured a certain
  way goes into ``concepts/architecture``. Use subfolders for specific topics like documentation or tests.
  - **Scope and Future Plans**:

    - **Scope**: Information about the scope of GeoIPS goes into ``concepts/scope``.
    - **Future Plans**: Information about future plans goes into ``concepts/future``.

Images/Supporting Files
-----------------------

If documentation requires support files beyond a single ``.rst`` file (eg. images),
please create a folder and place the support files and the documentation file in side of it.
The documentation file should be named ``index.rst`` and the folder should be named
descriptively. This setup is for clean URLs in built documentation.

Note
----

If none of the above paths fit your documentation, please consult with the team to find the appropriate location.
