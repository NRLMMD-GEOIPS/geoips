# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Workflow interface module."""

import logging

from geoips.interfaces.base import BaseYamlInterface
from geoips.filenames.base_paths import PATHS as gpaths

LOG = logging.getLogger(__name__)


class WorkflowsInterface(BaseYamlInterface):
    """Interface for workflow plugins."""

    name = "workflows"
    use_pydantic = gpaths["GEOIPS_USE_PYDANTIC"]
    # validator = WorkflowPluginModel

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
