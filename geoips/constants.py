# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Scientific and data-processing constants used across GeoIPS."""

# used as secondary default value in OBP Pydantic models processing
# OBP uses this to transform the fields as omitted ones so that
# module plugins can populate the arguments with required default values accordingly
PLUGIN_PROVIDED = "plugin_provided"
