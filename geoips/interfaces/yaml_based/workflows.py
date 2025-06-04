# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Workflow interface module."""

import logging
from pydantic import BaseModel


from geoips.interfaces.base import BaseYamlInterface
from geoips.models.workflows import WorkflowPluginModel


LOG = logging.getLogger(__name__)


class WorkflowsInterface(BaseYamlInterface):
    """Interface for workflow plugins."""

    name = "workflows"
    validator = WorkflowPluginModel
    use_pydantic = True


workflows = WorkflowsInterface()
