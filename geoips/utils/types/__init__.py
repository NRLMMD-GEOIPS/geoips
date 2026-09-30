# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Types subpackage init file.

The imports below trigger registration of the shared
``TypeConverterRegistry`` and all built-in / extended converters
at import time so that both ``DataTreeDitto`` and the
plugin-lifecycle hooks can discover them.

.. note::

    In a future version the import-time side-effects should be
    replaced with explicit ``register_converters()`` calls from the
    framework bootstrap entry point.
"""

from geoips.utils.types.converter_registry import (  # noqa: F401
    TypeConverterRegistry,
    converter_registry,
)
from geoips.utils.types.converters import FamilyConversionSpec  # noqa: F401
from geoips.utils.types import datatree_converters  # noqa: F401, E402
