# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Class-based, base plugins init file."""

# Note all imports from geoips.interfaces.class_based.bases below will error on
# flake8 F401: "imported but unused", since we are not including the
# individual module name strings in the __all__ variable below.
# flake8 does not recognize the list of strings when passed to
# __all__.  Note F401 is ignored on this file in geoips/.config/flake8,
# so when using the "official" GeoIPS flake8 config, these errors will
# not be reported. Since flake8 does not allow you to specify a single
# error to ignore within the full file (only ALL errors within the file,
# or single errors on a single line), we are ignoring F401 in this file
# via a per-file ignore within the flake8 config.
# https://stackoverflow.com/questions/48153886/flake8-ignore-specific-warning-for-entire-file

from geoips.interfaces.class_based.bases.algorithms import BaseAlgorithmPlugin
from geoips.interfaces.class_based.bases.colormappers import BaseColormapperPlugin
from geoips.interfaces.class_based.bases.coverage_checkers import (
    BaseCoverageCheckerPlugin,
)
from geoips.interfaces.class_based.bases.databases import BaseDatabasePlugin
from geoips.interfaces.class_based.bases.filename_formatters import (
    BaseFilenameFormatterPlugin,
)
from geoips.interfaces.class_based.bases.interpolators import BaseInterpolatorPlugin
from geoips.interfaces.class_based.bases.output_checkers import BaseOutputCheckerPlugin
from geoips.interfaces.class_based.bases.output_formatters import (
    BaseOutputFormatterPlugin,
)
from geoips.interfaces.class_based.bases.procflows import BaseProcflowPlugin
from geoips.interfaces.class_based.bases.readers import BaseReaderPlugin
from geoips.interfaces.class_based.bases.sector_adjusters import (
    BaseSectorAdjusterPlugin,
)
from geoips.interfaces.class_based.bases.sector_metadata_generators import (
    BaseSectorMetadataGeneratorPlugin,
)
from geoips.interfaces.class_based.bases.sector_spec_generators import (
    BaseSectorSpecGeneratorPlugin,
)
from geoips.interfaces.class_based.bases.title_formatters import (
    BaseTitleFormatterPlugin,
)
from geoips.interfaces.class_based.bases.validators import BaseValidatorPlugin

# These lists are the "master" lists of the interface names.
# These are used in validating the plugins (ie, so we will catch a typo
# in an interface name)
class_based_plugins = [
    "algorithms",
    "colormappers",
    "coverage_checkers",
    "databases",
    "filename_formatters",
    "interpolators",
    "output_checkers",
    "output_formatters",
    "procflows",
    "readers",
    "sector_adjusters",
    "sector_metadata_generators",
    "sector_spec_generators",
    "title_formatters",
    "validators",
]

# Note due to the fact that we are including all of the imported packages
# in __all__ via variables rather than the actual strings, flake8 does
# not recognize the above imports as being used.  F401 ignored via
# per-file ignore in geoips/.config/flake8 config.  See comment above
# for more information.
__all__ = class_based_plugins
