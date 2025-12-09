.. dropdown:: Distribution Statement

 This source code is subject to the license referenced at
 https://github.com/NRLMMD-GEOIPS.

.. _configuration:

Configuring GeoIPS
******************

Alike many other software packages, we offer the ability to precisely configure your
GeoIPS environment. This is largely done via the use of environment variables. As
referenced in our :ref:`installation docs<installing-geoips>`, we note how users must
set a few environment variables in order for GeoIPS to be aware of where to read data
from and where to store it (I.e. $GEOIPS_TESTDATA_DIR and $GEOIPS_OUTDIRS, respectively).

There are other types of environment variables as well, that aren't specifically tied to
GeoIPS. For example, on a linux machine you can set an $EDITOR environment variable,
which specifies what text editor you'd like to use whenever you open up a file. You'll
notice that this variable is more of a system wide configuration, rather than tied to a
specific software package.

In the following sections, we'll detail GeoIPS-specific environment variables and
system-wide environment variables that GeoIPS recognizes.

GeoIPS Environment Variables
============================

# TODO: Add content to this section.

System-Wide Environment Variables
=================================

GeoIPS recognizes a subset of system-wide environment variables. We'll detail what each
variable accomplishes below.

NO_COLOR
--------

``NO_COLOR`` disables any colored output from your operating terminal. Many software
packages, including GeoIPS, may have some commands which color certain portions of their
terminal output. Some users may not prefer this, and in that case, you can set this
variable to True in your .bashrc or comparable settings file.

Enabling this to True will prevent the GeoIPS commandline interface (CLI) from coloring
any of its terminal output (such as the beta warning after each GeoIPS command).

By default, if not set in your .bashrc, GeoIPS will not color any of its terminal output.

To set this environment variable, there are two options:

Temporary
^^^^^^^^^

Running the command below will disable colored terminal output for a single session.

.. code-block:: bash

    export NO_COLOR='True'

Persistent
^^^^^^^^^^

Running the command below will disable colored terminal output for all future sessions
until it is manually disabled.

.. code-block:: bash

    vim ~/.bashrc
    # Add the following line to your .bashrc
    export NO_COLOR='True'
    source ~/.bashrc
    # Reactivate your environment (I.e. conda activate geoips)
