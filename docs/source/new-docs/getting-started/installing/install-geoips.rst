:orphan:

Install GeoIPS
--------------

We can use ``pip`` to install all GeoIPS Python dependencies, and GeoIPS itself.

First, clone the GeoIPS git repository:

.. code:: bash

    git clone https://github.com/NRLMMD-GeoIPS/geoips.git $GEOIPS_PACKAGES_DIR/geoips

.. code:: bash

    # Ensure geoips python environment enabled before installing geoips
    pip install "$GEOIPS_PACKAGES_DIR/geoips"

If you want to install GeoIPS with all optional dependencies, you can use:

.. code:: bash

    # Ensure geoips python environment enabled before installing geoips
    pip install "$GEOIPS_PACKAGES_DIR/geoips[doc,lint,test,debug]"

The optional dependencies are:

- ``doc``: for building the documentation with Sphinx
  (the documentation is also available online at
  https://nrlmmd-geoips.github.io/geoips/)
- ``lint``: for linting the code (useful for developers)
- ``test``: for running the tests
- ``debug``: for debugging the code with IPython/jupyter