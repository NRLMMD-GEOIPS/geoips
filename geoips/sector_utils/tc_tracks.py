# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Modules to access TC tracks, based on locations found in the deck files."""

import logging

from geoips.interfaces import (
    sector_metadata_generators,
    sector_spec_generators,
    sectors,
)

LOG = logging.getLogger(__name__)

# If we ever revert back to numbered storm from named storm, we may need to include this
# list in "get_final_storm_name" rather than just INVEST
# UNNAMED_STORM_NAMES = ['invest', 'one', 'two', 'three', 'four', 'five', 'six',
#                        'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve',
#                        'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen',
#                        'eighteen', 'nineteen', 'twenty', 'twenty-one']


def create_tc_sector_info_dict(
    clat,
    clon,
    synoptic_time,
    storm_year,
    storm_basin,
    storm_num,
    aid_type=None,
    storm_name=None,
    final_storm_name=None,
    deck_line=None,
    source_sector_file=None,
    pressure=None,
    vmax=None,
):
    """Create storm info dictionary from items.

    Parameters
    ----------
    clat : float
        center latitude of storm
    clon : float
        center longitude of storm
    synoptic_time : datetime.datetime
        time of storm location
    storm_year : int
        4 digit year of storm
    storm_basin : str
        2 digit basin identifier
    storm_num : int
        2 digit storm number
    aid_type : str, default=None
        type of TC aid (BEST, MBAM, etc)
    storm_name : str, default=None
        Common name of storm
    final_storm_name : str, default=None
        Final name found throughout entire track file (ie, if reprocessing,
        will ensure early storm locations are identified with final storm name)
    deck_line : str, default=None
        source deck line for storm information
    pressure : float, default=None
        minimum pressure
    vmax : float, default=None
        maximum wind speed

    Returns
    -------
    fields : dict
        Dictionary of sector information, as passed into function.
    """
    fields = {}
    fields["clat"] = clat
    fields["clon"] = clon
    fields["synoptic_time"] = synoptic_time
    fields["storm_year"] = storm_year
    fields["storm_basin"] = storm_basin
    fields["storm_num"] = int(storm_num)
    fields["storm_name"] = "unknown"
    fields["aid_type"] = "unknown"
    fields["final_storm_name"] = "unknown"
    fields["source_sector_file"] = "unknown"
    if aid_type:
        fields["aid_type"] = aid_type
    if storm_name:
        fields["storm_name"] = storm_name
    if final_storm_name:
        LOG.info("USING passed final_storm_name %s", final_storm_name)
        fields["final_storm_name"] = final_storm_name
    else:
        LOG.info("USING storm_name as final_storm_name %s", storm_name)
        fields["final_storm_name"] = storm_name
    if source_sector_file:
        from geoips.geoips_utils import replace_geoips_paths

        fields["source_sector_file"] = replace_geoips_paths(source_sector_file)
    fields["pressure"] = pressure
    fields["deck_line"] = deck_line
    fields["vmax"] = vmax
    fields["source_filename"] = fields["source_sector_file"]
    fields["parser_name"] = None
    return fields


def get_tc_area_id(fields, finalstormname, tcyear):
    """Get TC area_id from fields, to be used as pyresample AreaDefinition area_id.

    Will be of form:
    * tcYYYYBBNNname (ie, tc2016io01one)
    """
    if not finalstormname:
        finalstormname = fields["storm_name"]
    newname = "{0}{1:02d}{2}".format(
        fields["storm_basin"].lower(), int(fields["storm_num"]), finalstormname.lower()
    )

    newname = newname.replace("_", "").replace(".", "").replace("-", "")

    # This ends up being tc2016io01one
    area_id = "tc" + str(tcyear) + newname
    return area_id


def get_tc_long_description(area_id, fields):
    """Return long_description of TC sector.

    This is commonly used as the long name/description on the
    pyresample AreaDefinition.
    """
    if "interpolated_time" in fields:
        long_description = "{0} interpolated_time {1}".format(
            area_id, str(fields["interpolated_time"])
        )
    else:
        long_description = "{0} synoptic_time {1}".format(
            area_id, str(fields["synoptic_time"])
        )
    return long_description


def set_tc_area_def(
    fields,
    tcyear=None,
    finalstormname=None,
    source_sector_file=None,
    clat=None,
    clon=None,
    tc_spec_template="tc_web",
    aid_type=None,
):
    """Set the TC area definition, using specified arguments.

    Parameters
    ----------
    fields : dict
        Dictionary of TC sector_info fields (clat, clon, storm name, etc)
        Valid fields can be found in geoips.sector_utils.utils.SECTOR_INFO_ATTRS
    tcyear : int, default=None
        Passed tcyear - since current year may not match tcyear for SHEM storms
    finalstormname : str, default=None
        finalstormname allows reprocessed storms to go in final storm directory
    source_sector_file : str, default=None
        attach source_sector_file to area_definition if known
    clat : float, default=None
        specify clat/clon separately from that found in 'fields'
    clon : float, default=None
        specify clat/clon separately from that found in 'fields'
    tc_spec_template: str, default="tc_web"
        Path to template YAML file to use when setting up area definition.
    aid_type : str, default=None
        type of TC aid (BEST, MBAM, etc)

    Returns
    -------
    pyresample.AreaDefinition
        pyresample AreaDefinition object with specified parameters.
    """
    if tc_spec_template is None:
        tc_spec_template = "tc_web"

    tc_template_plugin = sectors.get_plugin(tc_spec_template)

    # I think this is probably what we will want.
    template_func_name = tc_template_plugin["spec"]["sector_spec_generator"]["name"]
    template_args = tc_template_plugin["spec"]["sector_spec_generator"]["arguments"]

    if not finalstormname and "final_storm_name" in fields:
        finalstormname = fields["final_storm_name"]
    if not source_sector_file and "source_sector_file" in fields:
        source_sector_file = fields["source_sector_file"]
    if not source_sector_file and "source_filename" in fields:
        source_sector_file = fields["source_filename"]
    if not tcyear:
        tcyear = fields["storm_year"]
    if clat is None:
        clat = fields["clat"]
    if clon is None:
        clon = fields["clon"]

    area_id = get_tc_area_id(fields, finalstormname, tcyear)
    long_description = get_tc_long_description(area_id, fields)

    # These are things like 'center_coordinates'
    template_func = sector_spec_generators.get_plugin(template_func_name)
    # Probably generalize this at some point. For now I know those are the
    # ones that are <template>
    template_args["area_id"] = area_id
    template_args["long_description"] = long_description
    template_args["clat"] = clat
    template_args["clon"] = clon
    area_def = template_func(**template_args)

    if "interpolated_time" in fields:
        area_def.sector_start_datetime = fields["interpolated_time"]
        area_def.sector_end_datetime = fields["interpolated_time"]
    else:
        area_def.sector_start_datetime = fields["synoptic_time"]
        area_def.sector_end_datetime = fields["synoptic_time"]
    area_def.sector_type = "tc"
    area_def.sector_info = {}

    # area_def.description is Python3 compatible,
    # and area_def.description is Python2 compatible
    area_def.description = long_description
    if not hasattr(area_def, "description"):
        area_def.description = long_description

    from geoips.geoips_utils import replace_geoips_paths

    area_def.sector_info["source_sector_file"] = replace_geoips_paths(
        source_sector_file
    )
    # area_def.sector_info['sourcetemplate'] = dynamic_templatefname
    # area_def.sector_info['sourcedynamicxmlpath'] = dynamic_xmlpath
    # FNMOC sectorfile doesn't have pressure
    for fieldname in fields.keys():
        area_def.sector_info[fieldname] = fields[fieldname]
    area_def.sector_info["storm_year"] = tcyear

    # If storm_name is undefined in the current deck line, set it to finalstormname
    if area_def.sector_info["storm_name"] == "" and finalstormname:
        LOG.debug(
            'USING finalstormname "%s" rather than deck storm name "%s"',
            finalstormname,
            area_def.sector_info["storm_name"],
        )
        area_def.sector_info["storm_name"] = finalstormname
        area_def.sector_info["final_storm_name"] = finalstormname

    LOG.debug("      Current TC sector: %s", fields["deck_line"])
    return area_def


def trackfile_to_area_defs(
    trackfile_name, trackfile_parser="bdeck_parser", tc_spec_template=None
):
    """Get TC area definitions for the specified text trackfile.

    Limit to optionally specified trackfile_sectorlist

    Parameters
    ----------
    trackfile : str
        Full path to trackfile, convert each line into a separate area_def
    trackfile_parser : str
        Parser to use from plugins.modules.sector_metadata_generators on trackfiles

    Returns
    -------
    list
        List of pyresample AreaDefinition objects
    """
    if trackfile_parser is None:
        trackfile_parser = "bdeck_parser"

    parser = sector_metadata_generators.get_plugin(trackfile_parser)

    all_fields, final_storm_name, tc_year = parser(trackfile_name)

    area_defs = []
    LOG.info("STARTING setting TC area_defs")
    for fields in all_fields:
        # area_defs += [set_tc_sector(fields, dynamic_templatefname, finalstormname,
        #               tcyear, sfname, dynamic_xmlpath)]
        area_defs += [
            set_tc_area_def(
                fields,
                tc_year,
                finalstormname=final_storm_name,
                source_sector_file=trackfile_name,
                tc_spec_template=tc_spec_template,
            )
        ]
    LOG.info("FINISHED setting TC area_defs")

    return area_defs


def interpolate_storm_location(interp_dt, longitudes, latitudes, synoptic_times):
    """Interpolate the storm location at a specific time.

    Based on a list of known locations and times
    """
    LOG.info(
        "interp_dt: %s\nlatitudes:\n%s\nlongitudes:\n%s\nsynoptic_times:\n%s",
        interp_dt,
        latitudes,
        longitudes,
        synoptic_times,
    )
