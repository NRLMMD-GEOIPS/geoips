# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Workflow interface module."""

import logging

from geoips.interfaces.base import BaseYamlInterface

# from geoips.pydantic_models.v1.workflows import WorkflowPluginModel

LOG = logging.getLogger(__name__)


class WorkflowsInterface(BaseYamlInterface):
    """Interface for workflow plugins."""

    name = "workflows"
    use_pydantic = True
    # validator = WorkflowPluginModel


workflows = WorkflowsInterface()
