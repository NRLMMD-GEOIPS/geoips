# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""WFABBA ascii data reader.

WFABBA is a geostationary fire product produced by SSEC
"""

# Python Standard Libraries
from datetime import datetime
import logging
from os.path import basename

# Third-Party Libraries
import numpy as np
import xarray

LOG = logging.getLogger(__name__)

interface = "readers"
family = "standard"
name = "wfabba_ascii"
source_names = ["abi", "ahi", "gvar", "seviri"]


def parse_header_line(line):
    """Parse header line."""
    # Remove white space and '###' from header line
    line = line.replace("### ", "").strip()
    line = line.replace("   ", "")
    # There could be multiple meta data entries per line.
    # Entries are separated by commas
    if "," in line:
        entries = line.split(", ")
    else:
        entries = [line]
    # meta data field and description are separated by ':'
    # Loop through entries and split into key and value
    parsed_line = {}
    for entry in entries:
        if ":" not in entry:
            # Return None if entry does not follow key: val format
            return None
        split_entry = entry.split(": ")
        if len(split_entry) == 1:
            key = split_entry[0]
            val = ""
        else:
            key, val = split_entry
        if key == "Code":
            # Add special handling to keep information on the
            # different code meanings
            codes = [
                "10 (30) - Processed Fire Pixel (Temporally filtered)",
                "11 (31) - Saturated Fire Pixel (Temporally filtered)",
                "12 (32) - Cloudy Fire Pixel (Temporally filtered)",
                "13 (33) - High Probability Fire Pixel (Temporally filtered)",
                "14 (34) - Medium Probability Fire Pixel (Temporally filtered)",
                "15 (35) - Low Probability Fire Pixel (Temporally filtered)",
            ]
            val = "\n".join(codes)
        parsed_line[key] = val
    return parsed_line


def read_wfabba_header(wfabba_file):
    """Read WFABBA header."""
    with open(wfabba_file, "r") as f:
        is_header = True
        header_length = 0
        header_meta = {}
        while is_header:
            line = f.readline()
            if line[:3] == "###":
                parsed_line = parse_header_line(line)
                if parsed_line:
                    header_meta.update(parsed_line)
                header_length += 1
            else:
                is_header = False
    header_meta["header length"] = header_length - 2
    full_time = f"{header_meta.pop('Date')} {header_meta.pop('Time')}"
    header_meta["datetime"] = datetime.strptime(full_time, "%Y%j %H:%M:%S UTC")
    return header_meta


def read_wfabba_text(wfabba_file):
    """Read WFABBA text from file wfabba_file into xarray Dataset."""
    xobj = xarray.Dataset()
    header_meta = read_wfabba_header(wfabba_file)
    text = np.genfromtxt(
        wfabba_file,
        delimiter=",",
        skip_header=header_meta["header length"],
        comments=None,
        dtype=str,
    )
    header_meta["units"] = {}
    if int(header_meta["Number of detected fires"]) > 0:
        col_names = text[0, :]
        col_units = text[1, :]
        for col_num, (col_name, col_unit) in enumerate(zip(col_names, col_units)):
            col_name = col_name.replace("### ", "").replace(" ", "").lower()
            col_unit = col_unit.replace("### ", "").replace(" ", "")
            data = text[2:, col_num].astype(float)
            xobj[col_name] = xarray.DataArray(data)
            header_meta["units"][col_name] = col_unit
        xobj["firetime"] = xarray.DataArray(
            [header_meta["datetime"]] * int(header_meta["Number of detected fires"])
        )
    xobj.attrs["start_datetime"] = header_meta["datetime"]
    xobj.attrs["end_datetime"] = header_meta["datetime"]
    xobj.attrs["source_file_datetimes"] = [header_meta["datetime"]]
    xobj.attrs["platform_name"] = header_meta["Satellite"]
    xobj.attrs["source_name"] = header_meta["Instrument"]
    xobj.attrs["data_provider"] = header_meta["Data source"]
    return xobj


def call(fnames, metadata_only=False, chans=None, area_def=None, self_register=False):
    """Read WFABBA ascii data from a list of filenames.

    WFABBA  ascii files contain list of fire detects with their latitude,
    longitude, and scan location

    Parameters
    ----------
    fnames : list
        * List of strings, full paths to files
    metadata_only : bool, default=False
        * Return before actually reading data if True
    chans : list of str, default=None
        * NOT YET IMPLEMENTED
        * List of desired channels (skip unneeded variables as needed).
        * Include all channels if None.
    area_def : pyresample.AreaDefinition, default=None
        * NOT YET IMPLEMENTED
        * Specify region to read
        * Read all data if None.
    self_register : str or bool, default=False
        * NOT YET IMPLEMENTED
        * register all data to the specified dataset id (as specified in the
          return dictionary keys).
        * Read multiple resolutions of data if False.

    Returns
    -------
    dict of xarray.Datasets
        * dictionary of xarray.Dataset objects with required Variables and
          Attributes.
        * Dictionary keys can be any descriptive dataset ids.

    See Also
    --------
    :ref:`xarray_standards`
        Additional information regarding required attributes and variables
        for GeoIPS-formatted xarray Datasets.
    """
    xarray_objs = []
    metadata = read_wfabba_header(fnames[0])
    end_metadata = read_wfabba_header(fnames[-1])
    geoips_attrs = {
        "area_definition": area_def,
        "start_datetime": metadata["datetime"],
        "end_datetime": end_metadata["datetime"],
        "vertical_data_type": "surface",
        "source_name": "wfabba",
        "data_provider": "ssec",
        "interpolation_radius_of_influence": 2000,
    }
    if area_def:
        geoips_attrs["area_id"] = area_def.area_id
    else:
        geoips_attrs["area_id"] = metadata.get("scene_id")

    meta_dataset = xarray.Dataset(attrs=dict(metadata, **geoips_attrs))
    if metadata_only:
        return {"METADATA": meta_dataset}

    for i, fname in enumerate(fnames):
        LOG.info("Reading %s" % fname)
        wfabba_xobj = read_wfabba_text(fname)
        wfabba_xobj.attrs["source_file_names"] = [basename(fname)]
        wfabba_xobj.attrs["sample_distance_km"] = 2
        wfabba_xobj.attrs = dict(wfabba_xobj.attrs, **geoips_attrs)
        xarray_objs.append(wfabba_xobj)

    if len(xarray_objs) > 1:
        start_times = [x.attrs["start_datetime"] for x in xarray_objs]
        end_times = [x.attrs["end_datetime"] for x in xarray_objs]
        xarray_dset = xarray.concat(xarray_objs, dim="dim_0")
        xarray_dset.attrs["start_datetime"] = min(start_times)
        xarray_dset.attrs["end_datetime"] = max(end_times)
        xarray_dset = xarray_dset.assign_coords({"time": start_times})
    else:
        xarray_dset = xarray_objs[0]
    return {"wfabba": xarray_dset, "METADATA": meta_dataset}
