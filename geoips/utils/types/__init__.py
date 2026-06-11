# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Types subpackage init file.

The ``datatree_converters`` import below triggers registration of dict and
DataArray round-trip converters with DataTreeDitto at import time.  In a
future version this should be replaced with an explicit ``register_converters()``
call from the framework initialisation entry point.
"""

from geoips.utils.types import datatree_converters  # noqa: F401  # see docstring
