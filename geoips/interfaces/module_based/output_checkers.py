# # # Distribution Statement A. Approved for public release. Distribution unlimited.
# # #
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # #
# # # This program is free software: you can redistribute it and/or modify it under
# # # the terms of the NRLMMD License included with this program. This program is
# # # distributed WITHOUT ANY WARRANTY; without even the implied warranty of
# # # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the included license
# # # for more details. If you did not receive the license, for more information see:
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/

"""Output Checkers interface module."""

from geoips.interfaces.base import BaseModuleInterface, BaseModulePlugin
import logging

LOG = logging.getLogger(__name__)


class OutputCheckersBase(BaseModulePlugin):
    """Output Checkers routines to apply when comparing data outputs."""


class OutputCheckersInterface(BaseModuleInterface):
    """Output Checkers routines to apply when comparing data outputs."""

    name = "output_checkers"
    required_args = {"standard": ["fname", "compare_product", "output_product"],
                     "print_gunzip": ["fobj", "gunzip_fname"],
                     "print_gzip": ["fobj", "gzip_fname"]}
    required_kwargs = {"standard": {}}
    allowable_kwargs = {"test_product": ["goodcomps", "badcomps", "compare_strings"],
                        "out_diffname": ["ext", "flag"],
                        "compare_outputs": ["test_product_func"]}
    plugin_class = OutputCheckersBase

    def get_checker(filename):
        from geoips.plugins.modules.output_checkers import (
            geotiff_checker,
            image_checker,
            netcdf_checker,
            text_checker,
        )
        output_checkers = [geotiff_checker, image_checker, netcdf_checker, text_checker]
        correct_checker = None
        checker_found = False
        for output_checker in output_checkers:
            checker_found = output_checker.correct_type()
            if checker_found:
                correct_checker = output_checker
                break
        if not checker_found:
            raise


compare_outputs = OutputCheckersInterface()
