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

"""Text based interfaces init file."""

from geoips.errors import PluginError

def get_required_attrs(fpath):
    """Get the required attributes needed for any GeoIPS Plugin.

    Required attributes include, 'interface', 'name', and 'family'.

    Parameters
    ----------
    fpath: str
        - The filepath to the associated text-based plugin.

    Returns
    -------
    attrs: dict
        - A dictionary of attributes required to define a text plugin
        - Includes ['interface', 'name', 'family', 'doc'] as its keys.
    """
    interface = None
    name = None
    family = None
    doc = None
    with open(fpath, "r") as tfile:
        for line in tfile.readlines():
            if line.strip()[0] == "#":
                # Line starting with # denotes the comment section which should
                # contain the required attributes
                poss_attr = line.strip().replace(
                    " ",
                    "",
                ).replace("\t", "").replace("#", "")
                if poss_attr.startswith("interface="):
                    interface = poss_attr.replace("interface=", "")
                elif poss_attr.startswith("name="):
                    name = poss_attr.replace("name=", "")
                elif poss_attr.startswith("family="):
                    family = poss_attr.replace("family=", "")
                else:
                    if doc is None:
                        doc = []
                    doc.append(line)
            if interface and name and family:
                break
            else:
                continue
    if not (interface and name and family and doc):
        err_str = f"Text Plugin found at {fpath} is missing 1+ of ['interface', "
        err_str += "'name', 'family']. Please make sure to set those attributes in "
        err_str += "your text plugin before using it."
        raise PluginError(err_str)
    else:
        # Convert docstring list to a multiline string.
        doc = "".join(doc)
    return {
        "interface": interface,
        "name": name,
        "family": family,
        "doc": doc,
        "plugin_type": "text_based"
    }
