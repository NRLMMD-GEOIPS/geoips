# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Class based-base plugins init file."""

from geoips.base_class_plugins.algorithms import BaseAlgorithmPlugin
from geoips.base_class_plugins.colormappers import BaseColormapperPlugin
from geoips.base_class_plugins.coverage_checkers import BaseCoverageCheckerPlugin
from geoips.base_class_plugins.databases import BaseDatabasePlugin
from geoips.base_class_plugins.filename_formatters import BaseFilenameFormatterPlugin
from geoips.base_class_plugins.interpolators import BaseInterpolatorPlugin
from geoips.base_class_plugins.output_checkers import BaseOutputCheckerPlugin
from geoips.base_class_plugins.output_formatters import BaseOutputFormatterPlugin
from geoips.base_class_plugins.procflows import BaseProcflowPlugin
from geoips.base_class_plugins.readers import BaseReaderPlugin
from geoips.base_class_plugins.sector_adjusters import BaseSectorAdjusterPlugin
from geoips.base_class_plugins.sector_metadata_adjusters import (
    BaseSectorMetadataAdjusterPlugin,
)
from geoips.base_class_plugins.sector_spec_generators import (
    BaseSectorSpecGeneratorPlugin,
)
from geoips.base_class_plugins.title_formatters import BaseTitleFormatterPlugin

__all__ = [
    "BaseAlgorithmPlugin",
    "BaseColormapperPlugin",
    "BaseCoverageCheckerPlugin",
    "BaseDatabasePlugin",
    "BaseFilenameFormatterPlugin",
    "BaseInterpolatorPlugin",
    "BaseOutputCheckerPlugin",
    "BaseOutputFormatterPlugin",
    "BaseProcflowPlugin",
    "BaseReaderPlugin",
    "BaseSectorAdjusterPlugin",
    "BaseSectorMetadataAdjusterPlugin",
    "BaseSectorSpecGeneratorPlugin",
    "BaseTitleFormatterPlugin",
]
