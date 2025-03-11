# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Utility for reading HRIT datasets."""

import os
import re
import codecs
import logging
import shutil
import operator
from functools import reduce
from copy import copy
from struct import unpack
from datetime import datetime, timedelta

from geoips.utils.context_managers import import_optional_dependencies

with import_optional_dependencies(loglevel="interactive"):
    """Attempt to import xRITDecompress from pyPublicDecompWT.

    Needed to decompress xRIT data types.
    """
    from pyPublicDecompWT import xRITDecompress

import numpy as np

log = logging.getLogger(__name__)

# interface = None indicates to the GeoIPS interfaces that this is not a valid
# plugin, and this module will not be added to the GeoIPS plugin registry.
# This allows including python modules within the geoips/plugins directory
# that provide helper or utility functions to the geoips plugins, but are
# not full GeoIPS plugins on their own.
interface = None


class HritDtype(object):
    """HRIT data type."""

    types = {
        "uint8": "u1",
        "uint16": ">u2",
        "uint32": ">u4",
        "uint64": ">u8",
        "int8": "i1",
        "int16": ">i2",
        "int32": ">i4",
        "int64": ">i8",
        "byte": "B",
        "unicode": "U",
    }

    def __getattr__(self, type_name):
        """Get hritdtype attr."""
        try:
            return np.dtype(self.types[type_name])
        except KeyError:
            if type_name[0:4] == "char":
                if len(type_name) > 4:
                    return np.dtype(">S{}".format(type_name[4:]))
                else:
                    return np.dtype(">S")
            raise HritError("Unknown data type: {}".format(type_name))


dtype = HritDtype()


def read10bit(buff):
    """Read 10 bit little endian data from a buffer.

    Returns
    -------
    int
        16 bit unsigned int.
    """
    while True:
        b = buff.read(5)
        if not len(b):
            break
        n = int(codecs.encode(b, "hex"), 16)
        p3 = n & 0x3FF
        n >>= 10
        p2 = n & 0x3FF
        n >>= 10
        p1 = n & 0x3FF
        n >>= 10
        p0 = n & 0x3FF
        yield p0
        yield p1
        yield p2
        yield p3


class HritError(Exception):
    """Raise exception when errors occur in reading xRIT data files."""

    def __init__(self, msg, code=None):
        """Initialize HritError."""
        self.code = code
        self.value = msg

    def __str__(self):
        """Hriterror str method."""
        if self.code:
            return "{}: {}".format(self.code, self.value)
        else:
            return self.value


class HritFile(object):
    """Hrit File class."""

    _file_type_map = {
        0: "image",
        1: "gts",
        2: "text",
        3: "encryptionKey",
        128: "prologue",
        129: "epilogue",
    }

    def __init__(self, fname):
        """Initialize HRIT File object."""
        # Test for file
        if not os.path.isfile(fname):
            raise IOError("No such file or directory: {}".format(fname))

        self._name = os.path.abspath(fname)
        self._dirname = os.path.dirname(self.name)
        self._basename = os.path.basename(self.name)

        # 20201207 'rb' required for binary read in Python 3
        self._fobj = open(self._name, "rb")

        # Construct the metadata block map
        # Some of these are static, others change from file to file
        self._block_map = {
            0: [
                ("block_num", dtype.uint8, 1),
                ("block_length", dtype.uint16, 1),
                ("type_code", dtype.uint8, 1),
                ("header_length", dtype.uint32, 1),
                ("data_length", dtype.uint64, 1),
            ],
            1: [
                ("block_num", dtype.uint8, 1),
                ("block_length", dtype.uint16, 1),
                ("bits_per_pixel", dtype.uint8, 1),
                ("num_samples", dtype.uint16, 1),
                ("num_lines", dtype.uint16, 1),
                ("compression", dtype.uint8, 1),
            ],
            2: [
                ("block_num", dtype.uint8, 1),
                ("block_length", dtype.uint16, 1),
                ("projection", dtype.char32, 1),
                ("sample_scale", dtype.int32, 1),
                ("line_scale", dtype.int32, 1),
                ("sample_offset", dtype.int32, 1),
                ("line_offset", dtype.int32, 1),
            ],
            3: [
                ("block_num", dtype.uint8, 1),
                ("block_length", dtype.uint16, 1),
                (
                    "data_definition",
                    getattr(dtype, "char{}".format(self.__block_len_minus_two(3))),
                    1,
                ),
            ],
            4: [
                ("block_num", dtype.uint8, 1),
                ("block_length", dtype.uint16, 1),
                (
                    "annotation",
                    getattr(dtype, "char{}".format(self.__block_len_minus_two(4))),
                    1,
                ),
            ],
            5: [
                ("block_num", dtype.uint8, 1),
                ("block_length", dtype.uint16, 1),
                (
                    "time",
                    getattr(dtype, "char{}".format(self.__block_len_minus_two(5))),
                    1,
                ),
            ],  # Unsure how to convert
            6: [
                ("block_num", dtype.uint8, 1),
                ("block_length", dtype.uint16, 1),
                (
                    "ancillary_text",
                    getattr(dtype, "char{}".format(self.__block_len_minus_two(6))),
                    1,
                ),
            ],
            7: [
                ("block_num", dtype.uint8, 1),
                ("block_length", dtype.uint16, 1),
                (
                    "key_header_info",
                    getattr(dtype, "char{}".format(self.__block_len_minus_two(7))),
                    1,
                ),
            ],
            128: [
                ("block_num", dtype.uint8, 1),
                ("block_length", dtype.uint16, 1),
                ("sc_id", dtype.uint16, 1),
                ("chan_id", dtype.uint8, 1),
                ("segment", dtype.uint16, 1),
                ("start_segment", dtype.uint16, 1),
                ("end_segment", dtype.uint16, 1),
                ("data_field_repr", dtype.uint8, 1),
            ],
            129: None,
        }

        # Read the metadata itself
        self._metadata = self.__read_metadata()

    @property
    def block_info(self):
        """Block info."""
        if not hasattr(self, "_block_info"):
            self._block_info = self.__read_metadata_block_info()
        return self._block_info

    def __block_len_minus_two(self, block_num):
        """
        Return the length of a header block minus 2.

        This is for reading to the end of the block. This may seem silly,
        but is mainly used to make the code above readable.
        """
        try:
            return self.block_info[block_num][1] - 2
        except KeyError:
            return 0

    @property
    def block_map(self):
        """Return block map."""
        return self._block_map

    @property
    def metadata(self):
        """Return metadata."""
        if not hasattr(self, "_metadata"):
            self._metadata = self._read_metadata()
        return self._metadata

    # @property
    # def full_disk_geolocation_metadata(self):
    #     if not hasattr(self, '_full_disk_geolocation_metadata'):
    #         geomet = {}
    #         geomet['ob_area'] = re.sub(r'\W+', '',
    #                                            self.metadata['block_2']['projection'])
    #         geomet['num_lines'] = self.metadata['block_1']['num_lines']
    #         geomet['num_samples'] = self.metadata['block_1']['num_samples']
    #         geomet['line_scale'] = self.metadata['block_2']['line_scale']
    #         geomet['sample_scale'] = self.metadata['block_2']['sample_scale']
    #         geomet['line_offset'] = geomet['num_lines'] / 2
    #         geomet['sample_offset'] = geomet['num_samples'] / 2
    #         geomet['projection'] = self.metadata['block_2']['projection']
    #         geomet['start_datetime'] = self.start_datetime
    #         # Grabs the sub point longitude from the projection in the form
    #         #   proj(sublon)
    #         geomet['sublon'] = float(re.search(r"\((.+)\)",
    #                                  self.metadata['block_2']['projection']).group(1))
    #         self._full_disk_geolocation_metadata = geomet
    #     return self._full_disk_geolocation_metadata

    @property
    def geolocation_metadata(self):
        """Return geolocation metadata."""
        if not hasattr(self, "_geolocation_metadata"):
            geomet = {}
            geomet["ob_area"] = re.sub(
                r"\W+", "", self.metadata["block_2"]["projection"]
            )
            geomet["num_lines"] = self.metadata["block_1"]["num_lines"]
            geomet["num_samples"] = self.metadata["block_1"]["num_samples"]
            geomet["line_scale"] = self.metadata["block_2"]["line_scale"]
            geomet["sample_scale"] = self.metadata["block_2"]["sample_scale"]
            geomet["line_offset"] = self.metadata["block_2"]["line_offset"]
            geomet["sample_offset"] = self.metadata["block_2"]["sample_offset"]
            geomet["projection"] = str(self.metadata["block_2"]["projection"])
            geomet["start_datetime"] = self.start_datetime
            # Grabs the sub point longitude from the projection in the form
            #   proj(sublon)
            geomet["sublon"] = float(
                re.search(r"\((.+)\)", self.metadata["block_2"]["projection"]).group(1)
            )
            self._geolocation_metadata = geomet
        return self._geolocation_metadata

    @property
    def prologue(self):
        """Return prologue."""
        if not hasattr(self, "_prologue"):
            self._prologue = None
            if self.file_type == "prologue":
                self._prologue = self._read_prologue()
        return self._prologue

    # @property
    # def data(self):
    #     if not hasattr(self, '_data'):
    #         self._data = None
    #         if self.file_type == 'image':
    #             self._data = self._read_image_data()
    #     return self._data

    @property
    def epilogue(self):
        """Return epilogue."""
        if not hasattr(self, "_epilogue"):
            self._epilogue = None
            if self.file_type == "epilogue":
                self._epilogue = self._read_epilogue()
        return self._epilogue

    @property
    def name(self):
        """Return name."""
        return self._name

    @property
    def dirname(self):
        """Return file dirname."""
        return self._dirname

    @property
    def basename(self):
        """Return file basename."""
        return self._basename

    @property
    def file_type(self):
        """Return file_type."""
        return self._file_type_map[self.metadata["block_0"]["type_code"]]

    @property
    def start_datetime(self):
        """Return start_datetime."""
        return self.annotation_metadata["start_datetime"]

    @property
    def band(self):
        """Return band specified in block_128, if it exists."""
        if "block_128" in self.metadata:
            return "B{:02d}".format(self.metadata["block_128"]["chan_id"])
        else:
            return None

    @property
    def segment(self):
        """Return segment specified in block_128, if it exists."""
        if "block_128" in self.metadata:
            return self.metadata["block_128"]["segment"]
        else:
            return None

    @property
    def annotation_metadata(self):
        """Return annotation metadata (ie, platform, start time, etc)."""
        field_names = [
            "type",
            "disseminationID",
            "_",
            "platform",
            "band",
            "segment",
            "start_datetime",
            "compression",
        ]
        fields = {
            name: part.strip("_")
            for name, part in zip(
                field_names, self.metadata["block_4"]["annotation"].split("-")
            )
            if name != "_"
        }
        fields["platform"] = fields["platform"].lower()
        fields["start_datetime"] = datetime.strptime(
            fields["start_datetime"], "%Y%m%d%H%M"
        )
        return fields

    @property
    def _parts(self):
        """Return parts of filename, split on '-'."""
        return self.basename.split("-")

    @property
    def compressed(self):
        """Return True if compressed, False if not."""
        if "C" in self._parts[-1]:
            return True
        else:
            return False

    def decompress(self, outdir):
        """
        Decompress an xRIT file and return a file handle.

        The file will be decompressed to `outdir` and read from there.

        Returns an HritFile instance for the decompressed file.
        If already decompressed, raises an HritError.
        """
        # If compressed, then decompress
        if self.compressed:
            parts = copy(self._parts)
            parts[-1] = "__"
            new_fname = os.path.join(outdir, "-".join(parts))
            log.debug("Copying file to {}".format(new_fname))
            shutil.copy(self.name, new_fname)

            prevdir = os.getcwd()
            os.chdir(outdir)
            xRITDecompress(self.name)
            os.chdir(prevdir)

            return HritFile(new_fname)

        else:
            raise HritError("File already decompressed.  Unable to decompress.")

    def __read_metadata_block_info(self):
        """
        Read information about metadata blocks.

        This includes info about metadata blocks including which blocks are present
        and their lengths.  Return a dictionary whose keys are metadata block numbers
        and whose values are tuple containing the block's starting byte number and its
        length in bytes.
        """
        # Get the full header length (4 bytes starting at 4th byte)
        buff = self._fobj
        buff.seek(4)
        header_length = unpack(">I", buff.read(4))[0]

        # Start from beginning of file
        buff.seek(0)
        # First block is always 0th block and starts at first byte
        block_info = {0: (0, 0)}
        # Loop over blocks until we hit the end of the header
        first_loop = True
        while buff.tell() < header_length:
            # Read the block number and block length
            block_start = buff.tell()
            block_num = unpack("B", buff.read(1))[0]
            block_length = unpack(">H", buff.read(2))[0]

            if first_loop:
                if block_num != 0:
                    raise HritError(
                        "This does not appear to be an HRIT file. "
                        f"The first block number should be 0 but we got {block_num}."
                    )
                first_loop = False

            # Add block_length for the current block
            block_info[block_num] = (block_start, block_length)

            # Seek to the end of the block
            buff.seek(block_start + block_length)

        return block_info

    def __read_metadata(self):
        """Read the metadata from the file and return as a dictionary."""
        metadata = {}
        for block_num in self.block_info.keys():
            # Get the block map for the current block number
            # If it is not found, warn
            try:
                block_map = self.block_map[block_num]
                if block_map is None:
                    log.debug(
                        "Skipping known, but undefined metadata block: {}".format(
                            block_num
                        )
                    )
                    continue
            except KeyError:
                log.warning(
                    "Unrecognized metadata block number encountered: {}".format(
                        block_num
                    )
                )
                continue

            # Create metadata dictionary for block
            block_md = {}

            # Seek to the correct starting position in the buffer
            block_start, block_len = self.block_info[block_num]
            self._fobj.seek(block_start)

            # Populate metadata dictionary based on map
            for field_name, dtype, count in block_map:
                block_md[field_name] = np.fromfile(self._fobj, dtype=dtype, count=count)
                # Strip padding from strings
                if dtype.char == "S":
                    newlist = []
                    for valnum, val in enumerate(block_md[field_name]):
                        if field_name == "time":
                            newlist += [val.strip()]
                        else:
                            newlist += [val.decode("ascii").strip().replace("\x05", "")]
                    block_md[field_name] = newlist
                # If there is only one value, then return a scalar rather than an array
                if count == 1:
                    block_md[field_name] = block_md[field_name][0]

            # Add to metadata dictionary
            metadata["block_{}".format(block_num)] = block_md

        return metadata

    def _read_image_data(self, sector=None):
        """Read image data."""
        log.debug("Reading image file: {}".format(self.name))
        if self.file_type != "image":
            raise HritError(
                "Unable to read image data from file of type {}".format(self.file_type)
            )

        # Get to the start of the line record
        header_length = self.metadata["block_0"]["header_length"]
        self._fobj.seek(header_length)

        self._data = np.fliplr(np.array(list(read10bit(self._fobj))).reshape(464, 3712))
        return self._data

    def _read_prologue(self, sector=None):
        """Read prologue file."""
        log.debug("Reading prologue file: {}".format(self.name))
        if self.file_type != "prologue":
            raise HritError(
                "Unable to read prologue data from file of type {}".format(
                    self.file_type
                )
            )

        # Get to the start of the header record
        self._fobj.seek(self.metadata["block_0"]["header_length"])

        prologue = {}

        # SatelliteStatus block
        prologue["satelliteStatus"] = {}
        prologue["satelliteStatus"]["satelliteDefinition"] = {}
        satdef = prologue["satelliteStatus"]["satelliteDefinition"]
        satdef["satelliteID"] = self.__rf(">u2")
        satdef["nominalLongitude"] = self.__rf(">f4")
        satdef["satelliteStatus"] = self.__rf(">u1")

        prologue["satelliteStatus"]["satelliteOperations"] = {}
        satops = prologue["satelliteStatus"]["satelliteOperations"]
        satops["lastManeuverFlag"] = self.__rf(">u1")
        satops["lastManeuverStartTime"] = self.__read_time_cds()
        satops["lastManeuverEndTime"] = self.__read_time_cds()
        satops["lastManeuverType"] = self.__rf(">u1")
        satops["nextManeuverFlag"] = self.__rf(">u1")
        satops["nextManeuverStartTime"] = self.__read_time_cds()
        satops["nextManeuverEndTime"] = self.__read_time_cds()
        satops["nextManeuverType"] = self.__rf(">u1")

        prologue["satelliteStatus"]["orbit"] = {}
        orbit = prologue["satelliteStatus"]["orbit"]
        orbit["periodStartTime"] = self.__read_time_cds()
        orbit["periodEndTime"] = self.__read_time_cds()
        orbit["orbitPolynomial"] = self.__read_orbit_polynomial()

        prologue["satelliteStatus"]["attitude"] = {}
        attitude = prologue["satelliteStatus"]["attitude"]
        attitude["periodStartTime"] = self.__read_time_cds()
        attitude["periodEndTime"] = self.__read_time_cds()
        attitude["principleAxisOffsetAngle"] = self.__rf(">f8")
        attitude["attitudePolynomial"] = self.__read_attitude_polynomial()

        prologue["satelliteStatus"]["spinRateatRCStart"] = self.__rf(">f8")

        prologue["satelliteStatus"]["utcCorrelation"] = {}
        utcCorr = prologue["satelliteStatus"]["utcCorrelation"]
        utcCorr["periodStartTime"] = self.__read_time_cds()
        utcCorr["periodEndTime"] = self.__read_time_cds()
        utcCorr["onBoardTimeStart"] = self.__rf(">u1", shape=(7,))
        utcCorr["varOnBoardTimeStart"] = self.__rf(">f8")
        utcCorr["a1"] = self.__rf(">f8")
        utcCorr["varA1"] = self.__rf(">f8")
        utcCorr["a2"] = self.__rf(">f8")
        utcCorr["varA2"] = self.__rf(">f8")

        # ImageAcquisition block
        prologue["imageAcquisition"] = {}
        prologue["imageAcquisition"]["plannedAcquisitionTime"] = {}
        acqTime = prologue["imageAcquisition"]["plannedAcquisitionTime"]
        acqTime["trueRepeatCycleStart"] = self.__read_time_cds(True)
        acqTime["plannedForwardScanEnd"] = self.__read_time_cds(True)
        acqTime["plannedRepeatCycleEnd"] = self.__read_time_cds(True)

        prologue["imageAcquisition"]["radiometerStatus"] = {}
        radioStat = prologue["imageAcquisition"]["radiometerStatus"]
        radioStat["channelStatus"] = self.__rf(">u1", shape=(12,))
        radioStat["detectorStatus"] = self.__rf(">u1", shape=(42,))

        prologue["imageAcquisition"]["radiometerSettings"] = {}
        radioSett = prologue["imageAcquisition"]["radiometerSettings"]
        radioSett["MDUSamplingDelays"] = self.__rf(">u2", shape=(42,))

        radioSett["hrvFrameOffsets"] = {}
        frameOff = radioSett["hrvFrameOffsets"]
        frameOff["MDUNomHRVDelay1"] = self.__rf(">u2")
        frameOff["MDUNomHRVDelay2"] = self.__rf(">u2")
        frameOff["spare"] = self.__rf("|S2")
        frameOff["MDUNomHRVBreakline"] = self.__rf(">u2")
        radioSett["DHSSSyncSelection"] = self.__rf(">u1")
        radioSett["MDUOutGain"] = self.__rf(">u2", shape=(42,))
        radioSett["MDUCourseGain"] = self.__rf(">u1", shape=(42,))
        radioSett["MDUFinegain"] = self.__rf(">u2", shape=(42,))
        radioSett["MDUNumericalOffset"] = self.__rf(">u2", shape=(42,))
        radioSett["PUGain"] = self.__rf(">u2", shape=(42,))
        radioSett["PUOffset"] = self.__rf(">u2", shape=(27,))
        radioSett["PUBias"] = self.__rf(">u2", shape=(15,))

        radioSett["operationParameters"] = {}
        operParam = radioSett["operationParameters"]
        operParam["L0_LineCounter"] = self.__rf(">u2")
        operParam["K1_RetraceLines"] = self.__rf(">u2")
        operParam["K2_PauseDeciseconds"] = self.__rf(">u2")
        operParam["K3_RetraceLines"] = self.__rf(">u2")
        operParam["K4_PauseDeciseconds"] = self.__rf(">u2")
        operParam["K5_RetraceLines"] = self.__rf(">u2")
        operParam["X_DeepSpaceWindowPosition"] = self.__rf(">u1")

        radioSett["refocusingLines"] = self.__rf(">u2")
        radioSett["refocusingDirection"] = self.__rf(">u1")
        radioSett["refocusingPosition"] = self.__rf(">u2")
        radioSett["scanRefPosFlag"] = self.__rf(">u1")
        radioSett["scanRefPosNumber"] = self.__rf(">u2")
        radioSett["scanRefPotVal"] = self.__rf(">f4")
        radioSett["scanFirstLine"] = self.__rf(">u2")
        radioSett["scanLastLine"] = self.__rf(">u2")
        radioSett["retraceStartLine"] = self.__rf(">u2")

        prologue["imageAcquisition"]["radiometerOperations"] = {}
        radioOper = prologue["imageAcquisition"]["radiometerOperations"]
        radioOper["lastGainChangeFlag"] = self.__rf(">u1")
        radioOper["lastGainChangeTime"] = self.__read_time_cds()

        radioOper["decontamination"] = {}
        dcon = radioOper["decontamination"]
        dcon["decontaminationNow"] = self.__rf(">u1")
        dcon["decontaminationStart"] = self.__read_time_cds()
        dcon["decontaminationEnd"] = self.__read_time_cds()

        radioOper["bbCalScheduled"] = self.__rf(">u1")
        radioOper["bbCalibrationType"] = self.__rf(">u1")
        radioOper["bbFirstLine"] = self.__rf(">u2")
        radioOper["bbLastLine"] = self.__rf(">u2")
        radioOper["coldFocalPlaneOpTemp"] = self.__rf(">u2")
        radioOper["warmFocalPlaneOpTemp"] = self.__rf(">u2")

        # CelestialEvents block
        prologue["celestialEvents"] = {}
        prologue["celestialEvents"]["celestialBodiesPosition"] = {}
        celestBod = prologue["celestialEvents"]["celestialBodiesPosition"]
        celestBod["periodStartTime"] = self.__read_time_cds()
        celestBod["periodEndTime"] = self.__read_time_cds()
        celestBod["relatedOrbitFileTime"] = self.__rf("|S15")
        celestBod["relatedAttitudeFileTime"] = self.__rf("|S15")
        celestBod["earthEphemeris"] = self.__read_ephemeris()
        celestBod["moonEphemeris"] = self.__read_ephemeris()
        celestBod["sunEphemeris"] = self.__read_ephemeris()
        celestBod["starEphemeris"] = self.__read_starcoeff()

        prologue["celestialEvents"]["relationToImage"] = {}
        relToImg = prologue["celestialEvents"]["relationToImage"]
        relToImg["typeOfEclipse"] = self.__rf(">u1")
        relToImg["eclipseStartTime"] = self.__read_time_cds()
        relToImg["eclipseEndTime"] = self.__read_time_cds()
        relToImg["visibleBodiesInImage"] = self.__rf(">u1")
        relToImg["bodiesCloseToFOV"] = self.__rf(">u1")
        relToImg["impactOnImageQuality"] = self.__rf(">u1")

        # ImageDescription block
        prologue["imageDescription"] = {}
        prologue["imageDescription"]["projectionDescription"] = {}
        projDesc = prologue["imageDescription"]["projectionDescription"]
        projDesc["typeOfProjection"] = self.__rf(">u1")
        projDesc["longitudeOfSSP"] = self.__rf(">f4")

        prologue["imageDescription"]["referenceGridVIS_IR"] = {}
        refGrdVI = prologue["imageDescription"]["referenceGridVIS_IR"]
        refGrdVI["numberOfLines"] = self.__rf(">i4")
        refGrdVI["numberOfColumns"] = self.__rf(">i4")
        refGrdVI["lineDirGridStep"] = self.__rf(">f4")
        refGrdVI["columnDirGridStep"] = self.__rf(">f4")
        refGrdVI["gridOrigin"] = self.__rf(">u1")

        prologue["imageDescription"]["referenceGridHRV"] = {}
        refGrdHR = prologue["imageDescription"]["referenceGridHRV"]
        refGrdHR["numberOfLines"] = self.__rf(">i4")
        refGrdHR["numberOfColumns"] = self.__rf(">i4")
        refGrdHR["lineDirGridStep"] = self.__rf(">f4")
        refGrdHR["columnDirGridStep"] = self.__rf(">f4")
        refGrdHR["gridOrigin"] = self.__rf(">u1")

        prologue["imageDescription"]["plannedCoverageVIS_IR"] = {}
        pldCovVI = prologue["imageDescription"]["plannedCoverageVIS_IR"]
        pldCovVI["southernLinePlanned"] = self.__rf(">i4")
        pldCovVI["northernLinePlanned"] = self.__rf(">i4")
        pldCovVI["easternLinePlanned"] = self.__rf(">i4")
        pldCovVI["westernLinePlanned"] = self.__rf(">i4")

        prologue["imageDescription"]["plannedCoverageHRV"] = {}
        pldCovHR = prologue["imageDescription"]["plannedCoverageHRV"]
        pldCovHR["lowerSouthLinePlanned"] = self.__rf(">i4")
        pldCovHR["lowerNorthLinePlanned"] = self.__rf(">i4")
        pldCovHR["lowerEastLinePlanned"] = self.__rf(">i4")
        pldCovHR["lowerWestLinePlanned"] = self.__rf(">i4")
        pldCovHR["upperSouthLinePlanned"] = self.__rf(">i4")
        pldCovHR["upperNorthLinePlanned"] = self.__rf(">i4")
        pldCovHR["upperEastLinePlanned"] = self.__rf(">i4")
        pldCovHR["upperWestLinePlanned"] = self.__rf(">i4")

        prologue["imageDescription"]["level15ImageProduction"] = {}
        l15Proj = prologue["imageDescription"]["level15ImageProduction"]
        l15Proj["imageProcDirection"] = self.__rf(">u1")
        l15Proj["plannedGenDirection"] = self.__rf(">u1")
        l15Proj["plannedChanProcessing"] = self.__rf(">u1", shape=(12,))

        # RadiometricProcessing block
        prologue["radiometricProcessing"] = {}
        prologue["radiometricProcessing"]["rpSummary"] = {}
        rpSumm = prologue["radiometricProcessing"]["rpSummary"]
        rpSumm["radianceLinearization"] = self.__rf(">u1", shape=(12,))
        rpSumm["detectorEqualization"] = self.__rf(">u1", shape=(12,))
        rpSumm["onboardCalibrationResult"] = self.__rf(">u1", shape=(12,))
        rpSumm["mpefCalFeedback"] = self.__rf(">u1", shape=(12,))
        rpSumm["mtfAdatption"] = self.__rf(">u1", shape=(12,))
        rpSumm["straylightCorrectionFlag"] = self.__rf(">u1", shape=(12,))

        prologue["radiometricProcessing"][
            "level15ImageCalibration"
        ] = self.__read_image_calibration()

        prologue["radiometricProcessing"]["blackBodyDataUsed"] = {}
        bbUsed = prologue["radiometricProcessing"]["blackBodyDataUsed"]
        bbUsed["bbObservationUTC"] = self.__read_time_cds(True)

        bbUsed["bbRelatedData"] = {}
        bbRelDat = bbUsed["bbRelatedData"]
        bbRelDat["onBoardBBTime"] = self.__rf(">u1", shape=(7,))
        bbRelDat["mduOutGain"] = self.__rf(">u2", shape=(42,))
        bbRelDat["mduCoarseGain"] = self.__rf(">u1", shape=(42,))
        bbRelDat["mduFineGain"] = self.__rf(">u2", shape=(42,))
        bbRelDat["mduNumericalOffset"] = self.__rf(">u2", shape=(42,))
        bbRelDat["PUGain"] = self.__rf(">u2", shape=(42,))
        bbRelDat["PUOffset"] = self.__rf(">u2", shape=(27,))
        bbRelDat["PUBias"] = self.__rf(">u2", shape=(15,))
        bbRelDat["dcrValues"] = self.__rf("|S63")
        bbRelDat["xDeepSpaceWindowPosition"] = self.__rf(">u1")

        bbRelDat["coldFPTempterature"] = {}
        coldFPT = bbRelDat["coldFPTempterature"]
        coldFPT["fcuNominalColdFocalPlaneTemp"] = self.__rf(">u2")
        coldFPT["fcuRedundantColdFocalPlaneTemp"] = self.__rf(">u2")

        bbRelDat["warmFPTempterature"] = {}
        warmFPT = bbRelDat["warmFPTempterature"]
        warmFPT["fcuNominalWarmFocalPlaneVHROTemp"] = self.__rf(">u2")
        warmFPT["fcuRedundantWarmFocalPlaneVHROTemp"] = self.__rf(">u2")

        bbRelDat["scanMirrorTemperature"] = {}
        scanMT = bbRelDat["scanMirrorTemperature"]
        scanMT["fcuNominalScanMirrorSensor1Temp"] = self.__rf(">u2")
        scanMT["fcuRedundantScanMirrorSensor1Temp"] = self.__rf(">u2")
        scanMT["fcuNominalScanMirrorSensor2Temp"] = self.__rf(">u2")
        scanMT["fcuRedundantScanMirrorSensor2Temp"] = self.__rf(">u2")

        bbRelDat["m1m2m3Temperature"] = {}
        m1m2m3 = bbRelDat["m1m2m3Temperature"]
        m1m2m3["fcuNominalM1MirrorSensor1Temp"] = self.__rf(">u2")
        m1m2m3["fcuRedundantM1MirrorSensor1Temp"] = self.__rf(">u2")
        m1m2m3["fcuNominalM1MirrorSensor2Temp"] = self.__rf(">u2")
        m1m2m3["fcuRedundantM1MirrorSensor2Temp"] = self.__rf(">u2")
        m1m2m3["fcuNominalM23AssemblySensor1Temp"] = self.__rf(">u1")
        m1m2m3["fcuRedundantM23AssemblySensor1Temp"] = self.__rf(">u1")
        m1m2m3["fcuNominalM23AssemblySensor2Temp"] = self.__rf(">u1")
        m1m2m3["fcuRedundantM23AssemblySensor2Temp"] = self.__rf(">u1")

        bbRelDat["baffleTemperature"] = {}
        baffTemp = bbRelDat["baffleTemperature"]
        baffTemp["fcuNominalM1BaffleTemp"] = self.__rf(">u2")
        baffTemp["fcuRedundantM1BaffleTemp"] = self.__rf(">u2")

        bbRelDat["blackBodyTemperature"] = {}
        bbTemp = bbRelDat["blackBodyTemperature"]
        bbTemp["fcuNominalBlackBodySensorTemp"] = self.__rf(">u2")
        bbTemp["fcuRedundantBlackBodySensorTemp"] = self.__rf(">u2")

        bbRelDat["fcuMode"] = {}
        fcuMode = bbRelDat["fcuMode"]
        fcuMode["fcuNominalSMMStatus"] = self.__rf("|S2")
        fcuMode["fcuRedundantSMMStatus"] = self.__rf("|S2")

        bbRelDat["extractedBBData"] = self.__read_extracted_bb_data()

        prologue["radiometricProcessing"][
            "mpefCalFeedback"
        ] = self.__read_impf_cal_data()

        prologue["radiometricProcessing"]["radTransform"] = self.__rf(
            ">f4", shape=(42, 64)
        )

        prologue["radiometricProcessing"]["radProcMTFAdaption"] = {}
        radAdapt = prologue["radiometricProcessing"]["radProcMTFAdaption"]
        radAdapt["vis_irMTFCorrectionE_W"] = self.__rf(">f4", shape=(33, 16))
        radAdapt["vis_irMTFCorrectionN_S"] = self.__rf(">f4", shape=(33, 16))
        radAdapt["hrfMTFCorrectionE_W"] = self.__rf(">f4", shape=(9, 16))
        radAdapt["hrvMTFCorrectionN_S"] = self.__rf(">f4", shape=(9, 16))
        radAdapt["straylightCorrection"] = self.__rf(">f4", shape=(12, 8, 8))

        # GeometricProcessing block
        prologue["geometricProcessing"] = {}
        prologue["geometricProcessing"]["optAxisDistances"] = {}
        optAxDist = prologue["geometricProcessing"]["optAxisDistances"]
        optAxDist["e-wFocalPlane"] = self.__rf(">f4", shape=(42,))
        optAxDist["n-sFocalPlane"] = self.__rf(">f4", shape=(42,))

        prologue["geometricProcessing"]["earthModel"] = {}
        earthMod = prologue["geometricProcessing"]["earthModel"]
        earthMod["typeOfEarthModel"] = self.__rf(">u1")
        earthMod["equatorialRadius"] = self.__rf(">f8")
        earthMod["northPolarRadius"] = self.__rf(">f8")
        earthMod["southPolarRadius"] = self.__rf(">f8")

        prologue["geometricProcessing"]["atmosphericModel"] = self.__rf(
            ">f4", shape=(12, 360)
        )
        prologue["geometricProcessing"]["resamplingFunctions"] = self.__rf(
            ">u1", shape=(12,)
        )

        self._prologue = prologue
        return self._prologue

    def _read_epilogue(self, sector=None):
        """Read epilogue file."""
        log.debug("Reading epilogue file: {}".format(self.name))
        if self.file_type != "epilogue":
            raise HritError(
                "Unable to read epilogue data from file of type {}".format(
                    self.file_type
                )
            )

        return None

    # Routine for reading specific things
    def __read_field(self, dtype, shape=(1,)):
        """Read field."""
        dtype = np.dtype(dtype)
        bytes_per_elem = dtype.itemsize
        nbytes = bytes_per_elem * reduce(operator.mul, shape, 1)

        dat = np.frombuffer(self._fobj.read(nbytes), dtype=dtype).reshape(shape)
        if dat.size == 1:
            dat = dat[0]

        return dat

    __rf = __read_field

    def __read_time_cds(self, expanded=False):
        """
        Read time CDS.

        Each self.__rf must remain, even if unused, since the reads increment
        the pointer.
        """
        epoch = datetime(1958, 1, 1, 0, 0, 0)
        days = self.__rf(">u2")
        millisec = self.__rf(">u4")
        # Must read in nanosec, even though it is never used.
        # Otherwise data will be out of sync from missing bytes in
        # the binary read.
        if expanded:
            microsec = self.__rf(">u2")
            nanosec = self.__rf(">u2")  # NOQA
        else:
            microsec = 0
            nanosec = 0  # NOQA
        time = epoch + timedelta(
            days=int(days), milliseconds=int(millisec), microseconds=int(microsec)
        )
        return time

    def __read_orbit_polynomial(self):
        """Read orbit polynomial."""
        poly = []
        for elemind in range(0, 100):
            elem = {
                "startTime": self.__read_time_cds(),
                "endTime": self.__read_time_cds(),
                "X": self.__rf(">f8", shape=(8,)),
                "Y": self.__rf(">f8", shape=(8,)),
                "Z": self.__rf(">f8", shape=(8,)),
                "VX": self.__rf(">f8", shape=(8,)),
                "VY": self.__rf(">f8", shape=(8,)),
                "VZ": self.__rf(">f8", shape=(8,)),
            }
            poly.append(elem)
        return poly

    def __read_attitude_polynomial(self):
        """Read attitude polynomial."""
        poly = []
        for elemind in range(0, 100):
            elem = {
                "startTime": self.__read_time_cds(),
                "endTime": self.__read_time_cds(),
                "XofSpinAxis": self.__rf(">f8", shape=(8,)),
                "YofSpinAxis": self.__rf(">f8", shape=(8,)),
                "ZofSpinAxis": self.__rf(">f8", shape=(8,)),
            }
            poly.append(elem)
        return poly

    def __read_ephemeris(self):
        """Read ephemeris."""
        ephem = []
        for elemind in range(0, 100):
            elem = {
                "startTime": self.__read_time_cds(),
                "endTime": self.__read_time_cds(),
                "alphaCoef": self.__rf(">f8", shape=(8,)),
                "betaCoef": self.__rf(">f8", shape=(8,)),
            }
            ephem.append(elem)
        return ephem

    def __read_starcoeff(self):
        """Read star coefficient."""
        coeff = []
        for coeffind in range(0, 100):
            stars = []
            for starind in range(0, 20):
                elem = {
                    "starID": self.__rf(">u2"),
                    "startTime": self.__read_time_cds(),
                    "endTime": self.__read_time_cds(),
                    "alphaCoef": self.__rf(">f8", shape=(8,)),
                    "betaCoef": self.__rf(">f8", shape=(8,)),
                }
                stars.append(elem)
            coeff.append(stars)
        return coeff

    def __read_image_calibration(self):
        """Read image calibration."""
        cal = []
        for chind in range(0, 12):
            chcal = {}
            chcal["slope"] = self.__rf(">f8")
            chcal["offset"] = self.__rf(">f8")
            cal.append(chcal)
        return cal

    def __read_extracted_bb_data(self):
        """Read extracted BB data."""
        bb_data = []
        for chind in range(0, 12):
            dat = {}
            dat["numberOfPixelsUsed"] = self.__rf(">u4")
            dat["meanCount"] = self.__rf(">f4")
            dat["rms"] = self.__rf(">f4")
            dat["maxCount"] = self.__rf(">u2")
            dat["minCount"] = self.__rf(">u2")
            dat["bbProcessingSlope"] = self.__rf(">f8")
            dat["bbProcessingOffset"] = self.__rf(">f8")
            bb_data.append(dat)
        return bb_data

    def __read_impf_cal_data(self):
        """Read IMPF Calibration data."""
        cal_data = []
        for chind in range(0, 12):
            cal = {}
            cal["imageQualityFlag"] = self.__rf(">u1")
            cal["referenceDataFlag"] = self.__rf(">u1")
            cal["absCalMethod"] = self.__rf(">u1")
            cal["pad1"] = self.__rf("|S1")
            cal["absCalWeightVic"] = self.__rf(">f4")
            cal["absCalWeightXsat"] = self.__rf(">f4")
            cal["absCalCoeff"] = self.__rf(">f4")
            cal["absCalError"] = self.__rf(">f4")
            cal["gscisCalCoeff"] = self.__rf(">f4")
            cal["gscisCalError"] = self.__rf(">f4")
            cal["gscisOffsetCount"] = self.__rf(">f4")
            cal_data.append(cal)
        return cal_data
