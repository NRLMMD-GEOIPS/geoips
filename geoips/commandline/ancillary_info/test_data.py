# # # Distribution Statement A. Approved for public release. Distribution is unlimited.
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

"""Ancillary module containing test dataset information."""

"""Dictionary mapping of GeoIPS Test Datasets.

Mapping goes {"test_dataset_name": "test_dataset_url"}
"""

interface = None  # denotes that this is not a plugin module

test_dataset_dict = {
    "test_data_fusion": r"https://io2.cira.colostate.edu/s/J73tEcn22smktMi/download?path=%2F&files=test_data_fusion.tgz",  # NOQA
    "test_data_noaa_aws": r"https://io2.cira.colostate.edu/s/J73tEcn22smktMi/download?path=%2F&files=test_data_noaa_aws.tgz",  # NOQA
    "test_data_amsr2": r"https://io2.cira.colostate.edu/s/J73tEcn22smktMi/download?path=%2F&files=test_data_amsr2_1.6.0.tgz",  # NOQA
    "test_data_clavrx": r"https://io2.cira.colostate.edu/s/J73tEcn22smktMi/download?path=%2F&files=test_data_clavrx_1.10.0.tgz",  # NOQA
    "test_data_gpm": r"https://io2.cira.colostate.edu/s/J73tEcn22smktMi/download?path=%2F&files=test_data_gpm_1.6.0.tgz",  # NOQA
    "test_data_sar": r"https://io2.cira.colostate.edu/s/J73tEcn22smktMi/download?path=%2F&files=test_data_sar_1.12.2.tgz",  # NOQA
    "test_data_scat": r"https://io2.cira.colostate.edu/s/J73tEcn22smktMi/download?path=%2F&files=test_data_scat_1.11.3.tgz",  # NOQA
    "test_data_smap": r"https://io2.cira.colostate.edu/s/J73tEcn22smktMi/download?path=%2F&files=test_data_smap_1.6.0.tgz",  # NOQA
    "test_data_viirs": r"https://io2.cira.colostate.edu/s/J73tEcn22smktMi/download?path=%2F&files=test_data_viirs_1.6.0.tgz",  # NOQA
}
