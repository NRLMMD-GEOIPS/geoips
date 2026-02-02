# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Output Checkers interface class."""

from geoips.base_class_plugins.output_checkers import (
    BaseOutputCheckerPlugin,
    is_gz,
    gunzip_product,
)
from geoips.interfaces.base import (
    BaseClassInterface,
    ValidationError,
)
import logging

# import subprocess

LOG = logging.getLogger(__name__)
rezip = False


class OutputCheckersInterface(BaseClassInterface):
    """Output Checkers routines to apply when comparing data outputs."""

    name = "output_checkers"
    required_args = {"standard": {}}
    required_kwargs = {"standard": {}}
    plugin_class = BaseOutputCheckerPlugin
    # required_args = {
    #     "standard": ["fname", "output_product", "compare_product"],
    #     "print_gunzip": ["fobj", "gunzip_fname"],
    #     "print_gzip": ["fobj", "gzip_fname"],
    # }
    # required_kwargs = {"standard": {}}
    # allowable_kwargs = {
    #     "test_product": ["goodcomps", "badcomps", "compare_strings"],
    #     "out_diffname": ["ext", "flag"],
    #     "compare_outputs": ["test_product_func"],
    # }

    def identify_checker(self, filename, checker_override_name=None):
        """Identify the correct output checker plugin and return its name.

        Parameters
        ----------
        filename : str
            - The name of the file to be checked against a comparison output.
        checker_override_name: str (default=None)
            - If set, specifies an output checker that should be used for the
              input, instead of trying to discover it from the file name. If
              the requested output checker is not found, fall back on trying
              to discover it from the file name.

        Returns
        -------
        string
            - The name of the discovered output checker.
        """
        plugin_names = [checker.module.name for checker in self.get_plugins()]
        # First, check if an override was requested for this file.
        if checker_override_name and checker_override_name in plugin_names:
            return self.get_plugin(checker_override_name).module.name

        checker_found = False
        checker_name = None
        if is_gz(filename):
            # NOTE: this is the first time gunzip is run on the current
            # product, so ensure we clobber what is already there.
            filename = gunzip_product(
                filename, is_comparison_product=False, clobber=True
            )
        for output_checker in self.get_plugins():
            checker_found = output_checker.module.correct_file_format(filename)
            if checker_found:
                checker_name = output_checker.module.name
                break
        if not checker_found:
            raise TypeError("There isn't an output checker built for this data type.")
        return checker_name

    def get_plugin(self, name, rebuild_registries=None):
        """Return the output checker plugin corresponding to checker_name.

        Parameters
        ----------
        name : str
            - The name the desired plugin.
        rebuild_registries: bool (default=None)
            - Whether or not to rebuild the registries if get_plugin fails. If set to
              None, default to what we have set in geoips.filenames.base_paths, which
              defaults to True. If specified, use the input value of rebuild_registries,
              which should be a boolean value. If rebuild registries is true and
              get_plugin fails, rebuild the plugin registry, call then call
              get_plugin once more with rebuild_registries toggled off, so it only gets
              rebuilt once.
        """
        plug = super().get_plugin(name, rebuild_registries)
        if self.valid_plugin(plug):
            return plug

    def valid_plugin(self, plugin):
        """Check the validity of the supplied output_checker plugin."""
        # NOTE: The following logic will need to change (likely to just
        # hasattr(plugin, <attr>)) once we fully convert to class-based. There will not
        # be a 'module' attribute of the plugin class once this conversion has occured.
        if (
            not hasattr(plugin.module, "outputs_match")
            or not hasattr(plugin.module, "correct_file_format")
            or not hasattr(plugin.module, "call")
        ):
            raise ValidationError(
                "The plugin returned is missing one or more of the following functions."
                "\n[outputs_match, correct_file_format, call]. Please create those "
                "before using this plugin."
            )
        return True


output_checkers = OutputCheckersInterface()
