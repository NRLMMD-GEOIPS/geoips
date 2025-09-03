.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

Core Pydantic Models
====================

.. contents::

These models are imported from ``geoips.pydantic.bases`` and rendered with
``sphinx_pydantic`` for a concise view of fields, defaults, and config.

.. note::
   This page requires the Sphinx extension ``sphinx_pydantic`` to be enabled in
   ``conf.py``. Make sure you have::

      extensions.append("sphinx_pydantic")

PrettyBaseModel
---------------

.. autopydantic_model:: geoips.pydantic.bases.PrettyBaseModel
   :model-show-field-summary: true
   :model-show-config-summary: true
   :model-show-json: true
   :model-show-validator-members: false

CoreBaseModel
-------------

.. autopydantic_model:: geoips.pydantic.bases.CoreBaseModel
   :model-show-field-summary: true
   :model-show-config-summary: true
   :model-show-json: true
   :model-show-validator-members: false

FrozenModel
-----------

.. autopydantic_model:: geoips.pydantic.bases.FrozenModel
   :model-show-field-summary: true
   :model-show-config-summary: true
   :model-show-json: true
   :model-show-validator-members: false

PermissiveFrozenModel
---------------------

.. autopydantic_model:: geoips.pydantic.bases.PermissiveFrozenModel
   :model-show-field-summary: true
   :model-show-config-summary: true
   :model-show-json: true
   :model-show-validator-members: false

PluginModel
-----------

.. autopydantic_model:: geoips.pydantic.bases.PluginModel
   :model-show-field-summary: true
   :model-show-config-summary: true
   :model-show-json: true
   :model-show-validator-members: false

DynamicModel
------------

.. autopydantic_model:: geoips.pydantic.bases.DynamicModel
   :model-show-field-summary: true
   :model-show-json: true

PermissiveDynamicModel
----------------------

.. autopydantic_model:: geoips.pydantic.bases.PermissiveDynamicModel
   :model-show-field-summary: true
   :model-show-config-summary: true
   :model-show-json: true
   :model-show-validator-members: false
