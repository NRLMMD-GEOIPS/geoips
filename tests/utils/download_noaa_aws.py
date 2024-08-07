"""Module which downloads specific test datasets from NOAA AWS S3."""

import argparse
from datetime import datetime
import os
from urllib import request
from xml.etree import ElementTree as ET

"""
Arguments needed for download:
* satellite=$1
* yyyy=$2
* mm=$3
* dd=$4
* hh=$5
* mn=$6

Optional Arguments for download:
* test_data_dir=$7
* wildcard_list=$8
"""


class NoaaAwsDataDownloader:
    """Class which is responsible for downloading datasets from NOAA AWS S3.

    Usually will download satellite-derived data, but there are other options as well
    such as GFS, Climatology Network Daily, and atmospheric science datasets.
    """

    test_save_dir = f"{os.environ['GEOIPS_TESTDATA_DIR']}/test_data_noaa_aws/data/"

    def __init__(self):
        """Initialize the NoaaAwsDataDownloader Class."""
        self.parser = self.get_parser()
        self.ARGS = self.parser.parse_args()
        self.bucket_path = str(
            f"https://noaa-{self.data_source_bucket_dict[self.ARGS.satellite_name]}"
            ".s3.amazonaws.com/"
        )

    @property
    def satellite_fname_dict(self):
        """Mapping of the filenaming date convention for each satellite we support."""
        if not hasattr(self, "_satellite_fname_dict"):
            self._satellite_fname_dict = {
                "geokompsat": "yyyymmddhhmn",
                "goes16": "yyyyjdatehhmn",
                "goes17": "yyyyjdatehhmn",
                "goes18": "yyyyjdatehhmn",
                "himawari8": "yyyymmdd_hhmn",
                "himawari9": "yyyymmdd_hhmn",
                "viirs": "yyyymmddmn",
            }
        return self._satellite_fname_dict

    @property
    def satellite_date_dict(self):
        """Mapping of the date storage-structure for each satellite we support."""
        if not hasattr(self, "_satellite_date_dict"):
            self._satellite_date_dict = {
                "geokompsat": "yyyymm/dd/hh/",
                "goes16": "yyyy/jdate/hh/",
                "goes17": "yyyy/jdate/hh/",
                "goes18": "yyyy/jdate/hh/",
                "himawari8": "yyyy/mm/dd/hhmn/",
                "himawari9": "yyyy/mm/dd/hhmn/",
                "viirs": "yyyy/mm/dd/",
            }
        return self._satellite_date_dict

    @property
    def satellite_sensor_dict(self):
        """Mapping of the sensors / products we currently support for each satellite."""
        if not hasattr(self, "_satellite_sensor_dict"):
            self._satellite_sensor_dict = {
                "geokompsat": ["AMI/L1B/FD/"],
                "goes16": ["ABI-L1b-RadF/"],
                "goes17": ["ABI-L1b-RadF/"],
                "goes18": ["ABI-L1b-RadF/"],
                "himawari8": ["AHI-L1b-FLDK/"],
                "himawari9": ["AHI-L1b-FLDK/"],
                "viirs": [
                    "VIIRS-DNB-GEO/",
                    "VIIRS-IMG-GEO-TC/",
                    "VIIRS-MOD-GEO-TC/",
                ],
            }
        return self._satellite_sensor_dict

    @property
    def data_source_bucket_dict(self):
        """A dictionary which maps data source names to AWS S3 Bucket Names."""
        if not hasattr(self, "_data_source_bucket_dict"):
            self._data_source_bucket_dict = {
                "geokompsat": "gk2a-pds",
                "goes16": "goes16",
                "goes17": "goes17",
                "goes18": "goes18",
                "himawari8": "himawari8",
                "himawari9": "himawari9",
                "viirs": "nesdis-n20-pds",
            }
            # self._data_source_bucket_dict = {
            #     "geokompsat": "gk2a-pds",
            #     "goes16": "goes16",
            #     "goes17": "goes17",
            #     "goes18": "goes18",
            #     "gfs": "gfs-bdp-pds",
            #     "himawari8": "himawari8",
            #     "himawari9": "himawari9",
            #     "hrrr": "hrrr-bdp-pds",
            #     "viirs": "nesdis-n20-pds",
            # }
        return self._data_source_bucket_dict

    def get_parser(self):
        """Retrieve the argument parser needed for downloading NOAA AWS Test Data."""
        parser = argparse.ArgumentParser("NOAA_AWS_DOWNLOADER")
        self.add_arguments(parser)
        return parser

    def add_arguments(self, parser):
        """Add NOAA AWS specific arguments to the supplied argparser.

        Parameters
        ----------
        parser: argparse.ArgumentParser
            - The parser we will be adding arguments to.
        """
        parser.add_argument(
            "satellite_name",
            type=str.lower,
            choices=list(self.data_source_bucket_dict.keys()),
            help="Source to retrieve data from.",
        )
        parser.add_argument(
            "year",
            type=str,
            help="The year in which the data derived from.",
        )
        parser.add_argument(
            "month",
            type=str,
            help="The month of the year in which the data was derived from.",
        )
        parser.add_argument(
            "day",
            type=str,
            help="The day of the month in which the data was derived from.",
        )
        parser.add_argument(
            "hour",
            type=str,
            help="The hour of the day in which the data was derived from.",
        )
        parser.add_argument(
            "minute",
            type=str,
            help="The minute of the day in which the data was derived from.",
        )
        parser.add_argument(
            "--save_dir",
            "-s",
            type=str,
            help="The directory to save your data to.",
        )
        parser.add_argument(
            "--wildcard_list",
            "-w",
            type=str,
            nargs="+",
            help="A 1+ length list of wildcards to filter out specific files.",
        )

    def list_data_files(self):
        """Retrieve a listing of data files found under the corresponding AWS Bucket.

        Where the bucket is determined based on the satellite_name provided.
        """
        fpaths = self.generate_file_dirs()
        fnames = []
        datestamp = self.replace_by_date(
            self.satellite_fname_dict[self.ARGS.satellite_name]
        )
        for fpath in fpaths:
            url = f"{self.bucket_path}?list-type=2&prefix={fpath}"
            # Get and decode the response from the given url
            response = request.urlopen(url).read().decode()
            try:
                root = ET.fromstring(response)
                namespace = root.tag.split("}")[0] + "}"
                keys = root.findall(f".//{namespace}Key")
                # where keys contain file names and other corresponding information
                for key in keys:
                    # for each xml key
                    if datestamp in key.text:
                        # if the file provided includes the correct time stamp, add the
                        # file to fnames.
                        fnames += [key.text]
                    # otherwise just continue on to the next file
            except ET.ParseError or Exception:
                raise ET.ParseError(
                    "Error parsing XML Response. Please make sure the file path "
                    "provided is valid."
                )
        return fnames

    def download_data(self):
        """Download the NOAA AWS data based on the arguments provided to self.parser."""
        fnames = self.list_data_files()
        save_dir = f"{self.test_save_dir}{self.ARGS.satellite_name}/"
        save_dir += f"{self.ARGS.year}{self.ARGS.month}{self.ARGS.day}/"
        save_dir += f"{self.ARGS.hour}{self.ARGS.minute}/"
        # save_dir will be the satellite/yyyymmdd/hhmn/
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        print(f"DOWNLOADING {self.ARGS.satellite_name} DATA ...")
        for idx, fname in enumerate(sorted(fnames)):
            # retrieve the date from that url and plase it in the corresponding save
            # location.
            request.urlretrieve(
                f"{self.bucket_path}{fname}",
                f"{save_dir}{os.path.basename(fname)}",
            )
            print("{:.2f} % Complete".format(((idx + 1) / len(fnames)) * 100))
        print(f"Done! You can find your files at '{save_dir}'.")

    def calendar_to_julian(self):
        """Convert the provided calendar date into a julian date (len=3)."""
        year = int(self.ARGS.year)
        month = int(self.ARGS.month)
        day = int(self.ARGS.day)
        date_obj = datetime(year, month, day)
        epoch = datetime(year, 1, 1)
        jdate = (date_obj - epoch).days + 1
        return "0" * (3 - len(str(jdate))) + str(jdate)  # insert 0's if len != 3

    def generate_file_dirs(self):
        """Given satellite and date, generate the correct filedirs(s) to the data."""
        fpaths = []
        satellite_name = self.ARGS.satellite_name
        date_structure = self.replace_by_date(self.satellite_date_dict[satellite_name])
        for sensor in self.satellite_sensor_dict[satellite_name]:
            fpaths.append(f"{sensor}{date_structure}")
        return fpaths

    def replace_by_date(self, date_structure):
        """Given a string, replace such string with the provided date values.

        For example, if date_structure == "yyyymm/dd/hh/" and the provided date values
        were:
        {"year": "2023", "month": "12", "day": "08", "hour": "03", "minute": "00"}
        then the replaced string would be "202312/08/03/".

        Parameters
        ----------
        date_structure: str
            - The string including a date format that you'll replace with real values.
        """
        date_structure = date_structure.replace("yyyy", self.ARGS.year)
        date_structure = date_structure.replace("mm", self.ARGS.month)
        date_structure = date_structure.replace("dd", self.ARGS.day)
        date_structure = date_structure.replace("hh", self.ARGS.hour)
        date_structure = date_structure.replace("mn", self.ARGS.minute)
        date_structure = date_structure.replace("jdate", self.calendar_to_julian())
        return date_structure


# To get all test data needed from NOAA AWS, call this module with these arguments!

# python download_noaa_aws.py geokompsat 2023 12 08 03 00
# python download_noaa_aws.py goes16 2020 09 18 19 50
# python download_noaa_aws.py goes16 2021 09 29 00 00
# python download_noaa_aws.py himawari8 2020 04 05 00 00

downloader = NoaaAwsDataDownloader()
downloader.download_data()
