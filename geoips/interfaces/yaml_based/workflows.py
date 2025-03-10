# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Workflow interface module."""

from copy import deepcopy
import logging

from geoips.interfaces.base import BaseYamlInterface
from geoips.pydantic.workflows import WorkflowPluginModel


LOG = logging.getLogger(__name__)


class WorkflowsInterface(BaseYamlInterface):
    """Interface for workflow plugins."""

    name = "workflows"
    validator = WorkflowPluginModel

    def get_plugin(self, name, rebuild_registries=None):
        """Retrieve a workflow plugin from the given name.

        Parameters
        ----------
        name: str
            - The name of the workflow plugin we want to retrieve.
        """
        plugin = super().get_plugin(name, rebuild_registries=rebuild_registries)
        steps = plugin["spec"]["steps"]
        final_steps = []
        for step in steps:
            if list(step.keys())[0] == "workflow":
                # Found a workflow step. Replace this with the contents of the workflow
                # requested
                curr_workflow = step.pop("workflow")
                workflow_name = curr_workflow["name"]
                workflow_spec = curr_workflow["spec"]
                # Using self here as embedded workflows could theoretically happen
                # infinitely. Recursion allows for this
                dsteps = self.get_plugin(workflow_name)["spec"]["steps"]
                for didx, dstep in enumerate(dsteps):
                    dstep_name = list(dstep.keys())[0]
                    if "steps" in workflow_spec:
                        # Steps aren't required. For example, if you want all of the
                        # steps from a default workflow, don't bother specifying 'steps'
                        for ostep in workflow_spec["steps"]:
                            ostep_name = list(ostep.keys())[0]
                            if ostep_name == dstep_name:
                                # If a key was found in both the default workflow and
                                # the workflow we're retrieving, then override the
                                # default recursively where conflicts occur. However,
                                # if a conflict is found, let's say for 'colormapper',
                                # don't just replace the default colormapper with the
                                # override colormapper. Only override where keys
                                # conflict, and add any default key / values that aren't
                                # present in the override dictionary
                                dsteps[didx] = self._deep_merge(deepcopy(dstep), ostep)
                final_steps.extend(dsteps)
            else:
                final_steps.append(step)

        plugin["spec"]["steps"] = final_steps

        return plugin

    def _deep_merge(self, default, override):
        """Recursively merges 'override' into 'default'.

        Keys in 'override' will override those in 'default', while preserving any keys
        in 'default' not present in 'override'.

        Parameters
        ----------
        default: dict
            - A dictionary whose values we will use as default
        override: dict
            - A dictionary whose values will override default if the same keys are found
        """
        for key, value in override.items():
            if (
                key in default
                and isinstance(default[key], dict)
                and isinstance(value, dict)
            ):
                # If both values are dictionaries, recursively merge
                self._deep_merge(default[key], value)
            else:
                # Otherwise, override or add the key-value pair from override
                default[key] = value
        return default


workflows = WorkflowsInterface()
