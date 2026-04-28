.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.


.. module:: PKGNAME
   :noindex:

{% if pkgname == "geoips" %}
{% set title = "GeoIPS |reg| Documentation" %}
{% else %}
{% set title = pkgtitle ~ " GeoIPS |reg| Plugin Package Documentation" %}
{% endif %}

{{ title }}
{{ "=" * title|length }}

**Date**: |today| **Version**: |release|

**Previous versions**: Documentation of previous PKGNAME versions are available at
`github.com/NRLMMD-GEOIPS <https://github.com/NRLMMD-GEOIPS/>`__.

**Useful links**:
`Source Repository <https://github.com/NRLMMD-GEOIPS/PKGNAME>`__ |
`GeoIPS License <https://github.com/NRLMMD-GEOIPS/geoips/blob/main/LICENSE>`__ |
`NRLMMD <https://www.nrlmry.navy.mil/>`__ |
`CIRA <https://www.cira.colostate.edu/>`__

{% if pkgname == "geoips" %}
Introduction
------------

GeoIPS (Geolocated Information Processing System) is an extensible, open-source
Python framework designed to process any dataset with latitude and longitude
coordinates. It is plugin-based, allowing users to easily extend its
functionality without modifying the core codebase. Users can add new plugins
for data reading, interpolation, processing algorithms, output formatting,
etc., enabling the generation of both imagery and structured data products.
Plugins can be employed in Python scripts/packages or configured in YAML files
to produce consistent, reliable, infrastructure-as-code Workflows.

Scientific workflows frequently require transforming geolocated data into
consistent imagery and derived products. Whether working with satellite
observations, model output, or field measurements, researchers and operational
centers must combine data reading, coordinate transformations, interpolation,
algorithm application, and output formatting into reproduceable pipelines.
These functions and their combined workflows are often implemented as ad-hoc
scripts that become very difficult to extend, reuse, and put into production.

GeoIPS is a plugin-based Python framework, originally designed for production
meteorological applications and currently used in real-time environments.
Since becoming open-source, we have worked to adapt GeoIPS for broader
community use and improve user experience. GeoIPS’ architecture is general to
any dataset that has associated latitude and longitude coordinates. The
package's two main goals are to help scientists avoid reinventing existing
functionality and to facilitate the transition of scientific work to those who
want to use it in production.

GeoIPS separates data reading, interpolation, processing algorithms,
output formatting, and other functions into plugins that can be pieced
together into novel and reproducible workflows. The system supports generation
of imagery and structured data products, enabling consistent transformation
from input geolocated data products to analysis- and publication-ready
outputs.

{% else %}
.. automodule:: PKGNAME
   :noindex:
{% endif %}

.. grid:: 1 2 2 2
    :gutter: 2

    .. grid-item-card:: Getting Started

        .. image:: _static/index_user_guide.png
           :alt: getting-started
           :scale: 25%
           :align: center

        A quick introduction to PKGNAME, including an overview of the
        package, system requirements, installation instructions, a quick
        start guide, and best practices.

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

        .. button-link:: PKGNAME_api/index.html
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

.. toctree::
    :maxdepth: 3
    :hidden:
    :titlesonly:

    GETTING-STARTED_OPTIONAL
    FUNCTIONALITY_OPTIONAL
    TUTORIALS_OPTIONAL
    ARCHITECTURE_OPTIONAL
    CONTRIBUTE_OPTIONAL
    CONTACT_OPTIONAL
    PKGNAME_api/index
    releases/index

.. |reg|    unicode:: U+000AE .. REGISTERED SIGN
