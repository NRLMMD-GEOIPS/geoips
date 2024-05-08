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

"""Ancillary module containing test dataset information."""

"""Dictionary mapping of GeoIPS Test Datasets.

Mapping goes {"test_dataset_name": "test_dataset_url"}
"""

interface = None # denotes that this is not a plugin module

test_dataset_dict = {
    "test_data_viirs": "https://io.cira.colostate.edu/s/mQ2HbE2Js4E9rba/download/test_data_viirs.tgz",  # noqa
    "test_data_smap": "https://io.cira.colostate.edu/s/CezXWwXg4qR2b94/download/test_data_smap.tgz",  # noqa
    "test_data_scat": "https://io.cira.colostate.edu/s/HyHLZ9F8bnfcTcd/download/test_data_scat.tgz",  # noqa
    "test_data_sar": "https://io.cira.colostate.edu/s/snxx8S5sQL3AL7f/download/test_data_sar.tgz",  # noqa
    "test_data_noaa_aws": "https://io.cira.colostate.edu/s/fkiPS3jyrQGqgPN/download/test_data_noaa_aws.tgz",  # noqa
    "test_data_gpm": "https://io.cira.colostate.edu/s/LT92NiFSA8ZSNDP/download/test_data_gpm.tgz",  # noqa
    "test_data_fusion": "https://io.cira.colostate.edu/s/DSz2nZsiPMDeLEP/download/test_data_fusion.tgz",  # noqa
    "test_data_clavrx": "https://io.cira.colostate.edu/s/ACLKdS2Cpgd2qkc/download/test_data_clavrx.tgz",  # noqa
    "test_data_amsr2": "https://io.cira.colostate.edu/s/FmWwX2ft7KDQ8N9/download/test_data_amsr2.tgz",  # noqa
}