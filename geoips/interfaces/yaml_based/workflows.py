# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Workflow interface module."""

# cspell: ignore soverrides

from collections.abc import Mapping
from copy import deepcopy
import logging

import yaml

from geoips.interfaces.base import BaseYamlInterface
from geoips.interfaces import output_checkers

LOG = logging.getLogger(__name__)


class WorkflowsInterface(BaseYamlInterface):
    """Interface for workflow plugins."""

    name = "workflows"
    use_pydantic = True  # Always use pydantic for workflows.

    ##########################################
    #                                        #
    #  START STRING-BASED OVERRIDES SECTION  #
    #                                        #
    ##########################################

    def global_override_type(self, value: str):
        """Ensure an override string fits the following format.

        Expected Format
        ---------------
        '<global_variable_name>=<some_value>'

        Parameters
        ----------
        value : str
            The full global override string for a geoips run order_based command.

        Returns
        -------
        override_dict : dict
            The validated contents of an override string in a dictionary.
        """
        try:
            lhs, rhs = value.split("=", 1)
        except ValueError:
            raise ValueError(
                f"Invalid format '{value}'. Expected '<global_variable_name>=<value>'"
            )

        return {
            "argument": lhs,
            # doing a yaml.safe_load attempts to cast the value into its correct type
            "value": yaml.safe_load(rhs),
        }

    def step_override_type(self, value: str):
        """Ensure an override string fits the following format.

        Expected Format
        ---------------
        '<step_id>.<string1>.<optional_string2>.<optional_string3>...=<some_value>'

        Parameters
        ----------
        value : str
            The full step override string for a geoips run order_based command.

        Returns
        -------
        override_dict : dict
            The validated contents of an override string in a dictionary.
        """
        try:
            lhs, rhs = value.split("=", 1)
        except ValueError:
            raise ValueError(
                f"Invalid format '{value}'. Expected '<step_id>.<...>=<value>'"
            )

        parts = lhs.split(".")

        if len(parts) < 2:
            raise ValueError(
                f"Invalid key '{lhs}'. Must have at least '<step_id>.<string>'"
            )

        step_id = parts[0]
        keys = parts[1:-1]
        argument = parts[-1]

        return {
            "step_id": step_id,
            "keys": keys,
            "argument": argument,
            # doing a yaml.safe_load attempts to cast the value into its correct type
            "value": yaml.safe_load(rhs),
        }

    def _set_nested(self, d, step_id, keys, argument, value):
        """Set a key value pair in a nested dictionary.

        Parameters
        ----------
        d : dict[dict]
            The nested dictionary to set a key, value pair in.
        keys : list[str]
            A list of keys to access the nested dictionaries.
        argument : str
            The final key to set value to.
        value : Any
            The value to assign to a key that's in a nested dictionary.

        Returns
        -------
        d : dict[dict]
            A nested dictionary.
        """
        if d.get("spec") and d.get("spec").get("steps"):
            keys = ["spec", "steps"] + keys
        current = d
        for key in [step_id] + keys:
            current = current.setdefault(key, {})
        current.setdefault("arguments", {})[argument] = value

        return d

    def _override_step(self, steps, override):
        """Override an argument of a given step.

        Parameters
        ----------
        steps : dict[dict]
            An ordered dictionary of steps to apply in a given workflow.
        override : Any
            The value of the override.

        Returns
        -------
        steps : dict[dict]
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

    def _override_global(self, steps, override):
        """Override an argument of a given global.

        Parameters
        ----------
        steps : dict[dict]
            An ordered dictionary of steps to apply in a given workflow.
        override : Any
            The value of the override.

        Returns
        -------
        steps : dict[dict]
            An overridden representation of 'steps'.
        """
        for id, step in steps.items():
            if step.get("kind") == "workflow" and step.get("spec", {}).get("steps"):
                step["spec"]["steps"] = self._override_global(
                    step["spec"]["steps"], override
                )
            else:
                steps[id]["arguments"][override["argument"]] = override["value"]
        return steps

    def _override_workflow_string_format(
        self,
        workflow,
        goverrides=[],
        soverrides=[],
        grab_bases=True,
    ):
        """Override a workflow plugin where applicable.

        Parameters
        ----------
        workflow : dict
            A dictionary representation of a workflow plugin.
        goverrides : list[str], optional
            A list of string global overrides.
        soverrides : list[str], optional
            A list of string step overrides.
        grab_bases : bool, optional
            Whether or not to use the override arguments specified in a workflow's
            'arguments' section. Defaults to True.

        Returns
        -------
        overridden : dict
            The overridden representation of 'workflow'.
        """
        steps = workflow["spec"]["steps"]
        if grab_bases:
            base_goverrides, base_soverrides = (
                self._convert_override_dict_to_string_format(workflow)
            )
            # Add CLI arguments at the end of the list, they will override if duplicates
            # occur
            goverrides = base_goverrides.extend(goverrides)
            soverrides = base_soverrides.extend(soverrides)

        wf_overrides = {
            "global": goverrides,
            "step": soverrides,
        }

        for override_type, overrides in wf_overrides.items():
            for override in overrides:
                if isinstance(override, str):
                    steps = getattr(self, f"_override_{override_type}")(
                        steps,
                        getattr(self, f"{override_type}_override_type")(override),
                    )
                else:
                    steps = getattr(self, f"_override_{override_type}")(steps, override)

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
        """Insert a key/value pair immediately after an existing key.

        This helper only preserves ordering. Callers are responsible for
        constructing and validating ``new_value`` before insertion.

        Parameters
        ----------
        steps : dict
            Workflow steps dictionary.
        target_key : str
            Existing step id to insert after.
        new_key : str
            New step id to insert.
        new_value : dict
            New step definition to insert.

        Returns
        -------
        dict
            Workflow steps dictionary with the new key/value pair inserted.
        """
        new_steps = {}
        inserted = False

        for key, value in steps.items():
            new_steps[key] = value

            if key == target_key:
                new_steps[new_key] = dict(new_value)
                inserted = True

        if not inserted:
            raise KeyError(f"Could not find key '{target_key}' for insertion.")

        return new_steps

    def _build_output_checker_step(self, target_key, target_step, override):
        """Build an output checker step from a workflow test override.

        Output checker overrides target an existing output formatter step. The
        generated checker depends on that formatter and receives ``compare_path``
        and ``threshold`` as call arguments.

        Parameters
        ----------
        target_key : str
            Step id of the output formatter being checked.
        target_step : dict
            Workflow step definition identified by ``target_key``.
        override : dict
            Output checker override from a workflow ``test.outputs`` section.

        Returns
        -------
        dict or None
            Output checker step definition, or ``None`` when no compare path was
            supplied and the checker should not be inserted.
        """
        if target_step.get("kind") != "output_formatter":
            raise ValueError(
                "Output checker overrides must target an output_formatter "
                f"step. Step '{target_key}' has kind '{target_step.get('kind')}'."
            )

        checker_step = dict(override)
        compare_path = checker_step.pop("compare_path", None)
        threshold = checker_step.pop("threshold", None)

        if not compare_path:
            LOG.warning(
                "WARNING: NO COMPARE PATH PROVIDED, NOT ADDING OUTPUT CHECKER "
                f"STEP AFTER STEP '{target_key}'."
            )
            return None

        if "name" in checker_step and "output_checker_name" in checker_step:
            raise ValueError("Specify only one of 'name' or 'output_checker_name'.")
        if "output_checker_name" in checker_step:
            checker_step["name"] = checker_step.pop("output_checker_name")

        checker_step["arguments"] = {"compare_path": compare_path}
        if threshold is not None:
            checker_step["arguments"]["threshold"] = threshold
        checker_step["depends_on"] = [target_key]
        checker_step["kind"] = "output_checker"

        if "name" not in checker_step:
            checker_step["name"] = output_checkers.identify_checker(compare_path)

        return checker_step

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
            # Detected leaf output checker override. Overriding. 'full_test_policy' is a
            # field that is unique to output checker overrides and step definitions
            if isinstance(value, Mapping) and "full_test_policy" in value:
                # Generate a unique step id based on how many output checker step ids
                # were encountered previously
                count = sum(
                    step_name.startswith("output_checker") for step_name in steps
                )
                oc_step_name = f"output_checker{count + 1}"

                try:
                    target_step = steps[key]
                except KeyError:
                    raise KeyError(f"Could not find key '{key}' for insertion.")

                checker_step = self._build_output_checker_step(key, target_step, value)
                if checker_step is None:
                    return steps

                return self._insert_after_key(
                    steps,
                    target_key=key,
                    new_key=oc_step_name,
                    new_value=checker_step,
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

    def _convert_override_dict_to_string_format(
        self,
        workflow,
        input_arguments=None,
        use_test_arguments=False,
    ):
        """
        Convert a workflow's test section overrides to string-based overrides.

        Parameters
        ----------
        workflow : dict
            A dictionary representation of a workflow plugin.
        input_arguments : dict, optional
            A dictionary of input override arguments from the commandline. Defaults to
            None.
        use_test_arguments : bool, optional
            Whether or not to default to the arguments specified in a workflow's 'test'
            section or to default to the arguments set in the top level of a workflow
            plugin.

        Returns
        -------
        goverrides : list[str]
            A list of global override strings.
        soverrides : list[str]
            A list of step override strings.
        """
        goverrides = []
        soverrides = []
        if use_test_arguments:
            arguments = (
                input_arguments
                if input_arguments
                else workflow.get("test", {}).get("arguments", {})
            )
        else:
            arguments = (
                input_arguments if input_arguments else workflow.get("arguments", {})
            )

        for override_key, overrides in arguments.items():
            if override_key.startswith("global"):
                override_type = "global"
            else:
                override_type = "step"
            if isinstance(overrides, dict):
                for argument, value in overrides.items():
                    if override_type == "global":
                        str_override = f"{argument}={value}"
                        goverrides.append(str_override)
                    else:
                        str_override = f"{override_key}.{argument}={value}"
                        soverrides.append(str_override)
            else:
                argument = override_key.split(".")[-1]
                value = overrides
                if override_type == "global":
                    str_override = f"{argument}={value}"
                    goverrides.append(str_override)
                else:
                    str_override = f"{override_key}={value}"
                    soverrides.append(str_override)

        return goverrides, soverrides

    def _override_workflow_dict_format(
        self,
        workflow,
        goverrides={},
        soverrides={},
        oc_overrides={},
        use_test_arguments=False,
    ):
        """Override a workflow plugin where applicable.

        Parameters
        ----------
        workflow : dict
            A dictionary representation of a workflow plugin.
        goverrides : dict, optional
            A dictionary of global overrides.
        soverrides : dict, optional
            A dictionary for step overrides.
        oc_overrides : dict, optional
            A dictionary for output_checker overrides.
        use_test_arguments : bool, optional
            Whether or not to default to the arguments specified in a workflow's 'test'
            section or to default to the arguments set in the top level of a workflow
            plugin.

        Returns
        -------
        overridden : dict
            The overridden representation of 'workflow'.
        """
        in_goverrides, in_soverrides = self._convert_override_dict_to_string_format(
            workflow,
            input_arguments={"global": goverrides}.update(soverrides),
            use_test_arguments=use_test_arguments,
        )
        goverrides, soverrides = self._convert_override_dict_to_string_format(
            workflow,
        )

        # Add CLI arguments at the end of the list, they will override if duplicates
        # occur
        if in_goverrides and any(set(in_goverrides).difference(set(goverrides))):
            goverrides.extend(in_goverrides)
        if in_soverrides and any(set(in_soverrides).difference(set(soverrides))):
            soverrides.extend(in_soverrides)

        workflow = self._override_workflow_string_format(
            workflow, goverrides, soverrides, grab_bases=False
        )

        steps = deepcopy(workflow["spec"]["steps"])

        output_overrides = (
            oc_overrides
            if oc_overrides
            else workflow.get("test", {}).get("outputs", {})
        )

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
        expanded_workflow : WorkflowPlugin type
            A dictionary representation of an expanded workflow plugin. Expanding means
            nested workflows and/or products have been fully generated and everything
            has been specified in a single workflow plugin.
        """
        if not expanded_workflow.get("test"):
            raise KeyError(
                f"Error: attemping to test workflow plugin {expanded_workflow['name']} "
                "but the plugin is missing a top level 'test' section."
            )

        expanded_workflow = self._override_workflow_dict_format(
            expanded_workflow,
            use_test_arguments=True,
        )

        # Import buried in order to avoid circular import error
        from geoips.pydantic_models.v1.workflows import WorkflowPluginModel

        # omit adding 'test' section as that has already been validated. All we care
        # about is validating the overridden 'steps' section.
        plugin_subset = {
            "name": expanded_workflow["name"],
            "interface": expanded_workflow["interface"],
            "family": expanded_workflow["family"],
            "docstring": expanded_workflow["docstring"],
            "package": expanded_workflow["package"],
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
        name : str
            The name of the workflow plugin.
        rebuild_registries : bool (default=None)
            Whether or not to rebuild the registries if get_plugin fails. If set to
            None, default to what we have set in geoips.filenames.base_paths, which
            defaults to True. If specified, use the input value of rebuild_registries,
            which should be a boolean value. If rebuild registries is true and
            get_plugin fails, rebuild the plugin registry, call then call
            get_plugin once more with rebuild_registries toggled off, so it only gets
            rebuilt once.
        _expand : private bool (default=False)
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
