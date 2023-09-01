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

"""Procflows interface module."""

from geoips.interfaces.base import BaseModuleInterface


class ProcflowsInterface(BaseModuleInterface):
    """Class-based interface for processing workflows (procflows).

    Proclows drive a specific collection of steps for a particular type of
    processing.  Currently available are:

    * single_source: single input type and single output type.
    * overlay: two input types (one for foreground and one for background),
      with a single output type.
    * config_based: efficient method for producing all possible outputs for a
      given set of data files.
    """

    name = "procflows"
    required_args = {"standard": ["fnames"]}
    required_kwargs = {"standard": ["command_line_args"]}


procflows = ProcflowsInterface()
