# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Workflow interface module."""

from geoips.interfaces.base import BaseYamlInterface
from geoips.filenames.base_paths import PATHS as gpaths


class WorkflowsInterface(BaseYamlInterface):
    """Interface for workflow plugins."""

    name = "workflows"
    use_pydantic = True


workflows = WorkflowsInterface()
