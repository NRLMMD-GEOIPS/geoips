# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Ancillary module containing test dataset information."""

"""Dictionary mapping of GeoIPS Test Datasets.

Mapping goes {"test_dataset_name": "test_dataset_url"}
"""

from os import environ

import yaml

interface = None  # denotes that this is not a plugin module

urls = yaml.safe_load(
    open(f"{environ['GEOIPS_PACKAGES_DIR']}/setup/test-data-urls.yaml", "r")
)

test_dataset_dict = urls["test_data_urls"]
