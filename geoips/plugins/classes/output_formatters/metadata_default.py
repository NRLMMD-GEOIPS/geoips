# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Default YAML metadata output format."""

from geoips.interfaces.class_based.output_formatters import BaseOutputFormatterPlugin

import logging

from geoips.filenames.base_paths import PATHS as gpaths
from geoips.geoips_utils import replace_geoips_paths
from geoips.sector_utils.yaml_utils import write_yamldict

LOG = logging.getLogger(__name__)


class MetadataDefaultOutputFormatterPlugin(BaseOutputFormatterPlugin):
    """Metadata Default Output formatter plugin class."""

    # Have the meta`data_default output unchanging - metadata_tc will pick up all the
    # fields in sector_info, so any tests that use metadata_tc will test the latest
    # iteration of the TC-specific outputs, and in general we will want to use
    # metadata_default to avoid unnecessarily changing all outputs.
    default_fields = [
        "adjustment_id",
        "aid_type",
        "archer_fdeck",  # This is from recenter_tc plugins which run ARCHER.
        "bounding_box",
        "clat",
        "clon",
        "deck_line",
        "final_storm_name",
        "interpolated_time",
        "invest_number",
        "parser_name",
        "pressure",
        "product_filename",
        "recenter_type",  # This is from the recenter_tc plugin package
        "sector_type",
        "source_file_names",
        "source_filename",
        "source_sector_file",
        "storm_basin",
        "storm_name",
        "storm_num",
        "storm_start_datetime",
        "storm_year",
        "synoptic_time",
        "vmax",
    ]

    interface = "output_formatters"
    family = "standard_metadata"
    name = "metadata_default"

    def call(
        self,
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
        return self.output_metadata_yaml(
            metadata_yaml_filename,
            area_def,
            xarray_obj,
            product_partial_path,
            output_dict,
            include_metadata_filename=include_metadata_filename,
        )

    def remove_non_default_metadata(self, sector_info):
        """Remove non default metadata from the sector_info dictionary.

        Ensure we have a consistent set of metadata to include in the metadata default
        output, to reduce unnecessary YAML metadata output comparison changes.
        """
        return_sector_info = {}
        for key in sector_info:
            if key in self.default_fields:
                LOG.info("Retaining key '%s' '%s'", key, sector_info[key])
                return_sector_info[key] = sector_info[key]
            else:
                LOG.info("Removing non default key '%s' '%s'", key, sector_info[key])
        return return_sector_info

    def output_metadata_yaml(
        self,
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
        sector_info = self.update_sector_info_with_default_metadata(
            area_def, xarray_obj, **sector_info_kwargs
        )
        # NOTE metadata_tc has it's own version of output_tc_metadata_yaml, so adding
        # this line here does NOT impact metadata_tc.  We CAN NOT remove non-default
        # metadata directly from update_sector_info_with_default_metadata, because
        # metadata_tc uses that one directly.
        sector_info = self.remove_non_default_metadata(sector_info)

        returns = write_yamldict(
            sector_info, metadata_fname, force=True, replace_geoips_paths=True
        )
        if returns:
            LOG.info("METADATASUCCESS Writing %s", metadata_fname)
        return returns


PLUGIN_CLASS = MetadataDefaultOutputFormatterPlugin
