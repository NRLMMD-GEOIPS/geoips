Linters
=======

GeoIPS uses several linting tools to maintain code quality and consistency. This document describes the linters, how to install them, and how to run them.

Available Linters
-----------------

Black
^^^^^
- **Purpose**: Code formatting
- **Configuration**: ``.config/black``
- **Description**: An uncompromising code formatter that ensures consistent Python code style.

Flake8
^^^^^^
- **Purpose**: PEP8 compliance and style checking
- **Configuration**: ``.flake8``
- **Plugins**:
  - ``flake8-docstrings``: Enforces numpy docstring standard
  - ``flake8-rst-docstrings``: Ensures docstrings are valid reStructuredText
  - ``flake8-rst``: Checks code snippets in RST files
- **Description**: A tool that checks Python code against style guide violations and programming errors.

Bandit
^^^^^^
- **Purpose**: Security linting
- **Configuration**: Default settings
- **Description**: A security linter that identifies common security issues in Python code.

Doc8
^^^^
- **Purpose**: RST linting
- **Configuration**: Default settings
- **Description**: A linter for reStructuredText files that checks for syntax and style issues in documentation.

Prettier
^^^^^^^^
- **Purpose**: Formatting for YAML, JSON, and other files
- **Configuration**: Default settings
- **Description**: An opinionated code formatter that supports multiple languages and file formats.

Other Linters Available
^^^^^^^^^^^^^^^^^^^^^^^
Some other tools are included in the lint extras but are not required:

- ``pylint``: Static code analysis
- ``pinkrst``: RST auto-formatting (helpful for passing Doc8)

Installation
------------

Install all linters using pip or Poetry with the lint extras:

.. code-block:: bash

    pip install geoips[lint]
    poetry install --extras lint


Running the Linters
-------------------

You can run linters directly using their command-line interfaces:

.. code-block:: bash

    # Format Python code
    black --config .config/black /path/to/code

    # Check Python style and errors
    flake8 /path/to/code

    # Security linting
    bandit -ll -r /path/to/code

    # Lint RST documentation
    doc8 /path/to/docs

    # Format configuration files
    prettier --write /path/to/files

Configuration
-------------

- **Black**: Configured in ``.config/black`` with project-specific settings
- **Flake8**: Configured in ``.flake8`` with:
  - max-line-length=88 (compatible with Black)
  - numpy docstring convention
  - Specific error ignores (E203, W503, E712)
  - File exclusions
- **Doc8**: Uses default settings
  - max-line-length=120
- **Prettier**: Uses default settings

Continuous Integration
----------------------

Linters are automatically run in CI workflows. All linters must pass before pull requests can be merged.
