:notoc:

.. GEOIPS PKGNAME documentation master file, created by

.. module:: PKGNAME
   :noindex:

****************************************************************
GeoIPS |reg| PKGNAME Documentation
****************************************************************

**Date**: |today| **Version**: |release|

**Previous versions**: Documentation of previous PKGNAME versions are available at
`github.com/NRLMMD-GEOIPS <https://github.com/NRLMMD-GEOIPS/>`__.

**Useful links**:
`Source Repository <https://github.com/NRLMMD-GEOIPS/PKGNAME>`__ |
`GeoIPS License <https://github.com/NRLMMD-GEOIPS/geoips/blob/main/LICENSE>`__ |
`NRLMMD <https://www.nrlmry.navy.mil>`__ |

:mod:`PKGNAME` is a free software program, United States Government NRLMMD licensed.

::

    Distribution Statement A. Approved for public release. Distribution is unlimited.

    Author:
    Naval Research Laboratory, Marine Meteorology Division

    This program is free software: you can redistribute it and/or modify it under
    the terms of the NRLMMD License included with this program. This program is
    distributed WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the included license
    for more details. If you did not receive the license, for more information see:
    https://github.com/U-S-NRL-Marine-Meteorology-Division/

.. automodule:: PKGNAME
   :noindex:

{% if not single_doc -%}
.. grid:: 1 2 2 2
    :gutter: 2

    .. grid-item-card:: Getting Started

        .. image:: _static/index_user_guide.png
           :alt: getting-started
           :scale: 25%
           :align: center

        The getting started guide can help you get started with using
        PKGNAME.

        .. button-link:: getting-started/index.html
            :ref-type: ref
            :color: secondary
            :expand:
            :click-parent:

            Getting Started

    .. grid-item-card:: The API reference guide

        .. image:: _static/index_api.png
           :alt: API Reference
           :scale: 25%
           :align: center

        The reference guide contains a detailed description of PKGNAME API.
        The reference describes how the methods work and which parameters can
        be used. It assumes that you have an understanding of the key concepts.

        .. button-link:: api/index.html
            :ref-type: ref
            :color: secondary
            :expand:
            :click-parent:

            API

    .. grid-item-card:: To the release notes

        .. image:: _static/index_contribute.png
           :alt: release notes
           :scale: 25%
           :align: center

        Change logs, versioning and contribution history.

        .. button-link:: releases/index.html
            :ref-type: ref
            :color: secondary
            :expand:
            :click-parent:

            Release Notes

{% endif %}
{% if single_doc and single_doc.endswith('.rst') -%}
.. toctree::
    :maxdepth: 3
    :titlesonly:

    {{ single_doc[:-4] }}
{% elif single_doc and single_doc.count('.') <= 1 %}
.. autosummary::
    :toctree: PKGNAME_api/

    {{ single_doc }}
{% elif single_doc %}
.. autosummary::
    :toctree: PKGNAME_api/

    {{ single_doc }}
{% else -%}
.. toctree::
    :maxdepth: 3
    :hidden:
    :titlesonly:
{% endif %}
{% if not single_doc %}
    getting-started/index
    tutorials/index
    concepts/index
    releases/index
    contribute/index
    PKGNAME_api/index
    contact
{% endif %}

.. |reg|    unicode:: U+000AE .. REGISTERED SIGN
