# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Workflow interface module."""

from geoips.interfaces.base import BaseYamlInterface


class WorkflowsInterface(BaseYamlInterface):
    """Interface for workflow plugins."""

    name = "workflows"


workflows = WorkflowsInterface()
