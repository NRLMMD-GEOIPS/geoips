# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Workflow interface module."""

import logging

from geoips.errors import PluginError
from geoips.interfaces.base import BaseYamlInterface
from geoips.filenames.base_paths import PATHS as gpaths

LOG = logging.getLogger(__name__)


class WorkflowsInterface(BaseYamlInterface):
    """Interface for workflow plugins."""

    name = "workflows"
    use_pydantic = gpaths["GEOIPS_USE_PYDANTIC"]
    # validator = WorkflowPluginModel

    def _set_nested(self, d, keys, argument, value):
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
        for key in keys:
            current = current.setdefault(key, {})
        current[argument] = value

        return current

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
        for step in steps:
            if step["kind"] == override["kind"]:
                step["arguments"][override["argument"]] = override["value"]

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
        for step in steps:
            if override["argument"] in step["arguments"]:
                step["arguments"][override["argument"]] = override["value"]
        return steps

    def _replace_contents_with_step(self, steps, override_type, override):
        """Replace a section of 'steps' with override for a given override type.

        Parameters
        ----------
        steps: dict[dict]
            An ordered dictionary of steps to apply in a given workflow.
        override_type: str
            The type of override type being applied.
        override: Any
            The value of the override.

        Returns
        -------
        steps: dict[dict]
            An overridden representation of 'steps'.
        """
        match override_type:
            case "steps":
                pass

        return steps

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

        for override_type, override_strs in expanded_workflow["test"]:
            pass

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
