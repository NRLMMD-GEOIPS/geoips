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
from geoips.interfaces import output_checkers

LOG = logging.getLogger(__name__)


class WorkflowsInterface(BaseYamlInterface):
    """Interface for workflow plugins."""

    name = "workflows"
    use_pydantic = True  # Always use pydantic for workflows.
    _token_oc_format = {"name": "token", "arguments": {}}

    ##########################################
    #                                        #
    #  START STRING-BASED OVERRIDES SECTION  #
    #                                        #
    ##########################################

    def _set_nested(self, d, step_id, keys, argument, value):
        """Set a key value pair in a nested dictionary.

        Parameters
        ----------
        d: dict[dict]
            The nested dictionary to set a key, value pair in.
        keys: list[str]
            A list of keys to access the nested dictionaries.
        argument: str
            The final key to set value to.
        value: Any
            The value to assign to a key that's in a nested dictionary.

        Returns
        -------
        d: dict[dict]
            A nested dictionary.
        """
        current = d
        for key in [step_id] + keys:
            current = current.get(key, {})
        current["arguments"][argument] = value

        return d

    def _override_step(self, steps, override):
        """Override an argument of a given step.

        Parameters
        ----------
        steps: dict[dict]
            An ordered dictionary of steps to apply in a given workflow.
        override: Any
            The value of the override.

        Returns
        -------
        steps: dict[dict]
            An overridden representation of 'steps'.
        """
        steps = self._set_nested(
            steps,
            override["step_id"],
            override["keys"],
            override["argument"],
            override["value"],
        )
        return steps

    def _override_kind(self, steps, override):
        """Override an argument of a given kind.

        Parameters
        ----------
        steps: dict[dict]
            An ordered dictionary of steps to apply in a given workflow.
        override: Any
            The value of the override.

        Returns
        -------
        steps: dict[dict]
            An overridden representation of 'steps'.
        """
        for id, step in steps.items():
            if Lexeme(step["kind"]).singular == Lexeme(override["kind"]).singular:
                if step.get("arguments"):
                    steps[id]["arguments"][override["argument"]] = override["value"]

        return steps

    def _override_global(self, steps, override):
        """Override an argument of a given global.

        Parameters
        ----------
        steps: dict[dict]
            An ordered dictionary of steps to apply in a given workflow.
        override: Any
            The value of the override.

        Returns
        -------
        steps: dict[dict]
            An overridden representation of 'steps'.
        """
        for id, step in steps.items():
            if step.get("arguments") and override["argument"] in step["arguments"]:
                steps[id]["arguments"][override["argument"]] = override["value"]
        return steps

    def _override_workflow_string_format(
        self,
        workflow,
        goverrides=[],
        koverrides=[],
        soverrides=[],
    ):
        """Override a workflow plugin where applicable.

        Parameters
        ----------
        workflow: dict
            A dictionary representation of a workflow plugin.
        goverrides: list[str], optional
            A list of string global overrides.
        koverrides: list[str], optional
            A list of string kind overrides.
        soverrides: list[str], optional
            A list of string step overrides.

        Returns
        -------
        overridden: dict
            The overridden representation of 'workflow'.
        """
        steps = workflow["spec"]["steps"]

        wf_overrides = {"globals": goverrides, "kinds": koverrides, "steps": soverrides}

        for override_type, overrides in wf_overrides.items():
            type_singular = Lexeme(override_type).singular
            for override in overrides:
                steps = getattr(self, f"_override_{type_singular}")(steps, override)

        workflow["spec"]["steps"] = steps

        return workflow

    ########################################
    #                                      #
    #  END STRING-BASED OVERRIDES SECTION  #
    #                                      #
    ########################################

    ########################################
    #                                      #
    #  START DICT-BASED OVERRIDES SECTION  #
    #                                      #
    ########################################

    def _insert_after_key(self, steps, target_key, new_key, new_value):
        """Insert a new key/value pair immediately after target_key.

        Parameters
        ----------
        steps : dict
            Workflow steps dictionary.
        target_key : str
            The key of the target step_id to insert an output checker step after.
        new_key : str
            The step_id out the output checker step to be added.
        new_value : dict
            A dictionary of output_checker overrides to add to 'new_key' step.

        Returns
        -------
        new_steps : dict
            Overridden steps dictionary with a new output_checker step.
        """
        new_steps = {}
        inserted = False

        for key, value in steps.items():
            new_steps[key] = value

            if key == target_key:
                try:
                    arguments = new_value.pop("output_checker_arguments")
                except KeyError:
                    arguments = new_value.pop("arguments", None)
                    if arguments is None:
                        raise PluginError(
                            "Error: input workflow plugin is improperly formatted "
                            "either in it's workflow test section."
                            f"Offending input value == {new_value}"
                        )
                new_steps[new_key] = new_value
                new_steps[new_key]["arguments"] = arguments
                new_steps[new_key]["name"] = output_checkers.identify_checker(
                    arguments["compare_path"]
                )
                new_steps[new_key]["kind"] = "output_checker"
                inserted = True

        if not inserted:
            raise KeyError(f"Could not find key '{target_key}' for insertion.")

        return new_steps

    def _apply_output_checker_override(self, steps, override):
        """Recursively apply output checker overrides.

        Parameters
        ----------
        steps : dict
            Workflow steps dictionary.
        override : dict
            Override structure that mirrors the workflow hierarchy.

        Returns
        -------
        dict
            Updated workflow steps.
        """
        if not isinstance(override, Mapping):
            return steps

        for key, value in override.items():
            # Detected leaf output checker override. Overriding. 'policy' is a field
            # that is unique to output checker overrides and step definitions
            if isinstance(value, Mapping) and "policy" in value:
                # Generate a unique step id based on how many output checker step ids
                # were encountered previously
                count = sum(
                    step_name.startswith("output_checker") for step_name in steps
                )
                oc_step_name = f"output_checker{count + 1}"

                return self._insert_after_key(
                    steps,
                    target_key=key,
                    new_key=oc_step_name,
                    new_value=value,
                )

            if isinstance(value, Mapping):
                try:
                    step = steps[key]
                except KeyError:
                    raise KeyError(
                        "Error: the requested override cannot access a given key, value"
                        f" pair because it does not exist. Missing key = '{key}'."
                    )

                if isinstance(step, Mapping):
                    updated = self._apply_output_checker_override(
                        step,
                        value,
                    )
                    # Child recursion may have rebuilt an ordered mapping
                    # (specifically when inserting an output checker).
                    if updated is not step:
                        steps[key] = updated

        return steps

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
                    # Step override being applied. Both override value and current step
                    # are both dictionaries, so apply this recursively
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

    def _override_workflow_dict_format(
        self,
        workflow,
        goverrides=None,
        koverrides=None,
        soverrides=None,
        oc_overrides=None,
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
        oc_overrides: dict, optional
            A dictionary for output_checker overrides.

        Returns
        -------
        overridden: dict
            The overridden representation of 'workflow'.
        """
        steps = deepcopy(workflow["spec"]["steps"])
        # Determine if a subset of overrides is to be applied.
        # This occurs when 'geoips run obp' is supplied with override flags
        overrides_to_apply = self._determine_overrides_to_apply(
            goverrides,
            koverrides,
            soverrides,
            oc_overrides,
        )
        # If no flags have been provided, this command should only be ran via
        # 'geoips test workflow <workflow_name>'. Apply all overrides present
        if not any(overrides_to_apply):
            overrides_to_apply = ["globals", "kinds", "steps", "outputs"]

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

        if oc_overrides:
            output_overrides = oc_overrides
        else:
            output_overrides = workflow.get("test", {}).get("outputs")

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

        if "outputs" in overrides_to_apply:
            # override with output_checker steps
            for step_id, override in output_overrides.items():
                steps = self._apply_output_checker_override(steps, {step_id: override})

        workflow["spec"]["steps"] = steps

        return workflow

    ######################################
    #                                    #
    #  END DICT-BASED OVERRIDES SECTION  #
    #                                    #
    ######################################

    def _determine_overrides_to_apply(
        self, goverrides=None, koverrides=None, soverrides=None, oc_overrides=None
    ):
        """Determine the types of overrides to apply to a workflow plugin.

        Parameters
        ----------
        goverrides: dict, optional
            A dictionary of global overrides.
        koverrides: dict, optional
            A dictionary of kind overrides.
        soverrides: dict, optional
            A dictionary for step overrides.
        oc_overrides: dict, optional
            A dictionary for output_checker overrides.

        Returns
        -------
        overrides_to_apply: list[str | None]
            A list of str / None representing the types of overrides to apply.
        """
        overrides_to_apply = [
            override_type if override else None
            for override_type, override in {
                "globals": goverrides,
                "kinds": koverrides,
                "steps": soverrides,
                "outputs": oc_overrides,
            }.items()
        ]

        return overrides_to_apply

    def _override_expanded_workflow(self, expanded_workflow):
        """Override the contents of an expanded workflow.

        During this process, if the plugin is found to have a test section, replace all
        relevant portions of the workflow plugin with the contents of the test section,
        revalidate the result of that replacement, then return the validated results.

        This overrides WorkflowsInterface:get_plugin as we need to support the
        replacement of select variables with the contents of the test section of a given
        workflow plugin.

        Parameters
        ----------
        expanded_workflow: WorkflowPlugin type
            A dictionary representation of an expanded workflow plugin. Expanding means
            nested workflows and/or products have been fully generated and everything
            has been specified in a single workflow plugin.
        """
        if not expanded_workflow.get("test"):
            raise KeyError(
                f"Error: attemping to test workflow plugin {expanded_workflow['name']} "
                "but the plugin is missing a top level 'test' section."
            )

        expanded_workflow = self._override_workflow_dict_format(expanded_workflow)

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
