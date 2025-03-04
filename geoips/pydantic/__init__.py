# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""GeoIPS order-based procflow pydantic models init file."""


from geoips.pydantic.bases import PluginModel
from geoips.pydantic.sectors import SectorPluginModel
from geoips.pydantic.workflows import WorkflowPluginModel


PluginModel = PluginModel
SectorPluginModel = SectorPluginModel
WorkflowPluginModel = WorkflowPluginModel
