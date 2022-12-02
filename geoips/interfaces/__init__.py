from geoips.interfaces.algorithms import algorithms, AlgorithmsInterfacePlugin
from geoips.interfaces.colormaps import colormaps, ColorMapsInterfacePlugin
from geoips.interfaces.filename_formatters import filename_formatters, FilenameFormattersInterfacePlugin
from geoips.interfaces.interpolators import interpolators, InterpolatorsInterfacePlugin
from geoips.interfaces.output_formats import output_formats, OutputFormatsInterfacePlugin
from geoips.interfaces.procflows import procflows, ProcflowsInterfacePlugin
from geoips.interfaces.readers import readers, ReadersInterfacePlugin
from geoips.interfaces.title_formatters import title_formatters, TitleFormattersInterfacePlugin

all = [algorithms, AlgorithmsInterfacePlugin,
       colormaps, ColorMapsInterfacePlugin,
       filename_formatters, FilenameFormattersInterfacePlugin,
       interpolators, InterpolatorsInterfacePlugin,
       output_formats, OutputFormatsInterfacePlugin,
       procflows, ProcflowsInterfacePlugin,
       readers, ReadersInterfacePlugin,
       title_formatters, TitleFormattersInterfacePlugin
       ]
