# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Ancillary module containing test dataset information.

Dictionary mapping of GeoIPS Test Datasets.

Mapping goes {"test_dataset_name": "test_dataset_url"}
"""

from pathlib import Path
import yaml
from typing import Dict

# This is not a plugin module
interface = None


def load_test_dataset_urls() -> Dict[str, str]:
    """
    Load test dataset URLs from the YAML configuration file.

    Returns
    -------
    Dict[str, str]
        Dictionary mapping test dataset names to their URLs
    """
    current_file_path = Path(__file__).resolve()
    url_file_path = current_file_path.parent / "test-data-urls.yaml"

    with open(url_file_path, "r") as file:
        urls = yaml.safe_load(file)

    return urls["test_data_urls"]


# Initialize the test dataset dictionary
test_dataset_dict = load_test_dataset_urls()
