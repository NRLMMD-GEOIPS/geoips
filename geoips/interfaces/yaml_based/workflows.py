# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Workflow interface module."""

# cspell: ignore koverrides soverrides

from collections.abc import Mapping
from copy import deepcopy
import logging

from lexeme_type.lexeme import Lexeme

from geoips.errors import PluginError
from geoips.interfaces.base import BaseYamlInterface

LOG = logging.getLogger(__name__)


class WorkflowsInterface(BaseYamlInterface):
    """Interface for workflow plugins."""

    name = "workflows"
    use_pydantic = True  # Always use pydantic for workflows.

    def _apply_step_override(self, steps, override):
        """Recursively apply step overrides.

        Parameters
        ----------
        steps: dict[dict]
            An ordered dictionary of steps to apply in a given workflow.
        override: dict[str, Any] or dict[dict]
            A dictionary of overrides that is either key: value or a dictionary that
            may contain one or more key: value pairs.

        Returns
        -------
        steps: dict[dict]
            An overridden representation of 'steps'.
        """
        # if the current override node is not a dictionary, just return
        if not isinstance(override, Mapping):
            return

        for key, value in override.items():
            # if an override key is missing from the given workflow, raise a KeyError
            if isinstance(value, Mapping):
                try:
                    step = steps[key]
                except KeyError:
                    raise KeyError(
                        "Error: the requested override cannot access a given key, value"
                        f" pair because it does not exist. Missing key = '{key}'."
                    )

                if isinstance(step, Mapping) and isinstance(value, Mapping):
                    self._apply_step_override(step, value)
            # Leaf value -> override directly
            else:
                steps["arguments"][key] = value

        return steps

    def _recursively_override(
        self,
        steps,
        id,
        argument_name,
        value,
        interface,
    ):
        """Override an argument for a step, kind, or global.

        Parameters
        ----------
        steps: dict[dict]
            An ordered dictionary of steps to apply in a given workflow.
        id: str
            The step identification name.
        argument_name: str
            The name of the argument to override.
        value: Any
            The value of the override.
        interface: str or None
            The name of an interface whose arguments to override.

        Returns
        -------
        steps: dict[dict]
            An overridden representation of 'steps'.
        """
        # If their are no arguments because a spec: steps is specified, then
        # recursively call
        if steps[id].get("spec", {}).get("steps"):
            for step_id in steps[id]["spec"]["steps"]:
                steps[id]["spec"]["steps"] = self._recursively_override(
                    deepcopy(steps[id]["spec"]["steps"]),
                    step_id,
                    argument_name,
                    value,
                    interface,
                )
        # Add the argument regardless of whether or not the plugin accepts it. It will
        # be removed during the _invoke method if it's not accepted.
        elif steps[id].get("arguments") is not None:
            # accepts an empty dictionary
            steps[id]["arguments"][argument_name] = value

        return steps

    def _apply_override(
        self,
        override_type,
        steps,
        argument_name,
        value,
        interface=None,
    ):
        """Override an argument for a step, kind, or global.

        Parameters
        ----------
        override_type: str
            The type of override being applied. One of ['globals', 'kinds', 'steps']
        steps: dict[dict]
            An ordered dictionary of steps to apply in a given workflow.
        argument_name: str
            The name of the argument to override.
        value: Any
            The value of the override.
        interface: str or None
            The name of an interface whose arguments to override.

        Returns
        -------
        steps: dict[dict]
            An overridden representation of 'steps'.
        """
        for id, step in steps.items():
            if override_type in ["globals", "steps"]:
                self._recursively_override(
                    steps,
                    id,
                    argument_name,
                    value,
                    interface,
                )
            elif override_type == "kinds":
                if Lexeme(step["kind"]).singular == Lexeme(interface).singular:
                    self._recursively_override(
                        steps,
                        id,
                        argument_name,
                        value,
                        interface,
                    )
        return steps

    def _override_workflow(
        self, workflow, goverrides=None, koverrides=None, soverrides=None
    ):
        """Override a workflow plugin where applicable.

        Parameters
        ----------
        workflow: dict
            A dictionary representation of a workflow plugin.
        goverrides: dict, optional
            A dictionary of global overrides.
        koverrides: dict, optional
            A dictionary of kind overrides.
        soverrides: dict, optional
            A dictionary for step overrides.

        Returns
        -------
        overridden: dict
            The overridden representation of 'workflow'.
        """
        steps = deepcopy(workflow["spec"]["steps"])
        # Determine if a subset of overrides is to be applied.
        # This occurs when 'geoips run obp' is supplied with override flags
        overrides_to_apply = [
            override_type if override else None
            for override_type, override in {
                "globals": goverrides,
                "kinds": koverrides,
                "steps": soverrides,
            }.items()
        ]
        # If no flags have been provided, this command should only be ran via
        # 'geoips test workflow <workflow_name>'. Apply all overrides present
        if not any(overrides_to_apply):
            overrides_to_apply = ["globals", "kinds", "steps"]

        if goverrides:
            global_overrides = goverrides
        else:
            global_overrides = workflow.get("test", {}).get("globals")

        if koverrides:
            kind_overrides = koverrides
        else:
            kind_overrides = workflow.get("test", {}).get("kinds")

        if soverrides:
            step_overrides = soverrides
        else:
            step_overrides = workflow.get("test", {}).get("steps")

        if "globals" in overrides_to_apply:
            # override globals
            for argument_name, value in global_overrides.items():
                steps = self._apply_override("globals", steps, argument_name, value)

        if "kinds" in overrides_to_apply:
            # override kinds
            for interface, overrides in kind_overrides.items():
                for argument_name, value in overrides.items():
                    steps = self._apply_override(
                        "kinds", steps, argument_name, value, interface
                    )

        if "steps" in overrides_to_apply:
            # override steps
            for step_id, override in step_overrides.items():
                steps = self._apply_step_override(steps, {step_id: override})

        # TODO: override outputs

        workflow["spec"]["steps"] = steps

        return workflow

    def get_test_plugin(self, name, rebuild_registries=None):
        """Get a workflow plugin by its name.

        During this process, if the plugin is found to have a test section, replace all
        relevant portions of the workflow plugin with the contents of the test section,
        revalidate the result of that replacement, then return the validated results.

        This overrides WorkflowsInterface:get_plugin as we need to support the
        replacement of select variables with the contents of the test section of a given
        workflow plugin.

        Parameters
        ----------
        name: str
            The name of the workflow plugin.
        rebuild_registries: bool (default=None)
            Whether or not to rebuild the registries if get_plugin fails. If set to
            None, default to what we have set in geoips.filenames.base_paths, which
            defaults to True. If specified, use the input value of rebuild_registries,
            which should be a boolean value. If rebuild registries is true and
            get_plugin fails, rebuild the plugin registry, call then call
            get_plugin once more with rebuild_registries toggled off, so it only gets
            rebuilt once.
        """
        expanded_workflow = self.plugin_registry.get_yaml_plugin(
            self,
            name,
            rebuild_registries=rebuild_registries,
            _expand=True,
        )
        if not expanded_workflow.get("test"):
            raise PluginError(
                f"Error: attemping to test workflow plugin {name} but the plugin is "
                "missing a top level 'test' section."
            )

        expanded_workflow = self._override_workflow(expanded_workflow)

        # Import buried in order to avoid circular import error
        from geoips.pydantic_models.v1.workflows import WorkflowPluginModel

        # omit adding 'test' section as that has already been validated. All we care
        # about is validating the overridden 'steps' section.
        plugin_subset = {
            "name": expanded_workflow["name"],
            "interface": expanded_workflow["interface"],
            "family": expanded_workflow["family"],
            "docstring": expanded_workflow["docstring"],
            "package": expanded_workflow["docstring"],
            "relpath": expanded_workflow["relpath"],
            "spec": expanded_workflow["spec"],
        }

        WorkflowPluginModel(**plugin_subset)

        return expanded_workflow

    def get_plugin(self, name, rebuild_registries=None, _expand=False):
        """Get a workflow plugin by its name.

        This overrides BaseYamlInterface:get_plugin as we need to support 'expand'
        functionality for the CLI command 'geoips expand <workflow>'.

        Parameters
        ----------
        name: str
            The name of the workflow plugin.
        rebuild_registries: bool (default=None)
            Whether or not to rebuild the registries if get_plugin fails. If set to
            None, default to what we have set in geoips.filenames.base_paths, which
            defaults to True. If specified, use the input value of rebuild_registries,
            which should be a boolean value. If rebuild registries is true and
            get_plugin fails, rebuild the plugin registry, call then call
            get_plugin once more with rebuild_registries toggled off, so it only gets
            rebuilt once.
        _expand: private bool (default=False)
            If true, fully expand the workflow plugin in place. Otherwise, load as is
            done usually. This should only be used for the 'geoips expand <workflow>'
            command.
        """
        return self.plugin_registry.get_yaml_plugin(
            self,
            name,
            rebuild_registries=rebuild_registries,
            _expand=_expand,
        )


workflows = WorkflowsInterface()
