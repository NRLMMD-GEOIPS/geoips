# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Workflow interface module."""

import logging

from geoips.interfaces.base import BaseYamlInterface

LOG = logging.getLogger(__name__)


class WorkflowsInterface(BaseYamlInterface):
    """Interface for workflow plugins."""

    name = "workflows"
    use_pydantic = True


workflows = WorkflowsInterface()
