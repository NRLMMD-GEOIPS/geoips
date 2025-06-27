# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Default YAML metadata output format."""

import logging

from geoips.filenames.base_paths import PATHS as gpaths
from geoips.geoips_utils import replace_geoips_paths
from geoips.sector_utils.yaml_utils import write_yamldict

LOG = logging.getLogger(__name__)

interface = "output_formatters"
family = "standard_metadata"
name = "metadata_default"


def call(
    area_def,
    xarray_obj,
    metadata_yaml_filename,
    product_filename,
    metadata_dir="metadata",
    basedir=gpaths["TCWWW"],
    output_dict=None,
    include_metadata_filename=False,
):
    """Produce metadata yaml file of sector info associated with final_product.

    Parameters
    ----------
    area_def : AreaDefinition
        Pyresample AreaDefintion object
    final_product : str
        Product that is associated with the passed area_def
    metadata_dir : str, default='metadata'
        Subdirectory name for metadata (using non-default allows for
        non-operational outputs)

    Returns
    -------
    str
        Metadata yaml filename, if one was produced.
    """
    from geoips.sector_utils.utils import is_sector_type

    if not is_sector_type(area_def, "tc"):
        return None
    # os.path.join does not take a list, so "*" it
    # product_partial_path = product_filename.replace(gpaths['TCWWW'],
    #   'https://www.nrlmry.navy.mil/tcdat')
    product_partial_path = replace_geoips_paths(product_filename)
    # product_partial_path = pathjoin(
    #   *final_product.split('/')[-5:-1]+[basename(final_product)])
    return output_metadata_yaml(
        metadata_yaml_filename,
        area_def,
        xarray_obj,
        product_partial_path,
        output_dict,
        include_metadata_filename=include_metadata_filename,
    )


def update_sector_info_with_default_metadata(
    area_def, xarray_obj, product_filename=None, metadata_filename=None
):
    """Update sector info found in "area_def" with standard metadata output.

    Parameters
    ----------
    area_def : AreaDefinition
        Pyresample AreaDefinition of sector information
    xarray_obj : xarray.Dataset
        xarray Dataset object that was used to produce product
    product_filename : str
        Full path to full product filename that this YAML file refers to

    Returns
    -------
    dict
        sector_info dict with standard metadata added
         * bounding box
         * product filename with wildcards
         * basename of original source filenames
    """
    sector_info = area_def.sector_info.copy()

    if hasattr(area_def, "sector_type") and "sector_type" not in sector_info:
        sector_info["sector_type"] = area_def.sector_type

    sector_info["bounding_box"] = {}
    sector_info["bounding_box"]["minlat"] = area_def.area_extent_ll[1]
    sector_info["bounding_box"]["maxlat"] = area_def.area_extent_ll[3]
    sector_info["bounding_box"]["minlon"] = area_def.area_extent_ll[0]
    sector_info["bounding_box"]["maxlon"] = area_def.area_extent_ll[2]
    sector_info["bounding_box"]["pixel_width_m"] = area_def.pixel_size_x
    sector_info["bounding_box"]["pixel_height_m"] = area_def.pixel_size_y
    sector_info["bounding_box"]["image_width"] = area_def.width
    sector_info["bounding_box"]["image_height"] = area_def.height
    sector_info["bounding_box"]["proj4_string"] = area_def.proj_str

    if product_filename:
        sector_info["product_filename"] = replace_geoips_paths(product_filename)
    if metadata_filename:
        sector_info["metadata_filename"] = replace_geoips_paths(metadata_filename)

    if "source_file_names" in xarray_obj.attrs.keys():
        sector_info["source_file_names"] = xarray_obj.source_file_names
    # Backwards compatibility, so the default metadata doesn't change.
    if "source_file_names" in xarray_obj.attrs.keys():
        sector_info["source_file_names"] = xarray_obj.source_file_names

    return sector_info


def output_metadata_yaml(
    metadata_fname,
    area_def,
    xarray_obj,
    product_filename=None,
    output_dict=None,
    include_metadata_filename=False,
):
    """Write out yaml file "metadata_fname" of sector info found in "area_def".

    Parameters
    ----------
    metadata_fname : str
        Path to output metadata_fname
    area_def : AreaDefinition
        Pyresample AreaDefinition of sector information
    xarray_obj : xarray.Dataset
        xarray Dataset object that was used to produce product
    productname : str
        Full path to full product filename that this YAML file refers to

    Returns
    -------
    str
        Path to metadata filename if successfully produced.
    """
    sector_info_kwargs = {}
    if include_metadata_filename:
        sector_info_kwargs["metadata_filename"] = metadata_fname
    if product_filename:
        sector_info_kwargs["product_filename"] = product_filename
    sector_info = update_sector_info_with_default_metadata(
        area_def, xarray_obj, **sector_info_kwargs
    )

    returns = write_yamldict(
        sector_info, metadata_fname, force=True, replace_geoips_paths=True
    )
    if returns:
        LOG.info("METADATASUCCESS Writing %s", metadata_fname)
    return returns
