# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit tests for file-skip logging in `ReadersInterface.read_data_to_xarray_dict`."""

import logging
from datetime import datetime

import pytest
from xarray import Dataset

from geoips.errors import NoValidFilesError
from geoips.interfaces import readers
from geoips.plugins.classes.readers.utils.hrit_reader import HritError

READERS_LOGGER = "geoips.interfaces.class_based.readers"
FAKE_DIR = "/fake/dir"
START_TIME = datetime(2026, 1, 1, 12, 0)


def _good_metadata(fnames):
    """Return reader-style metadata for `fnames`, all at `START_TIME`."""
    return {
        "METADATA": Dataset(
            attrs={
                "start_datetime": START_TIME,
                "end_datetime": START_TIME,
                "source_file_names": list(fnames),
            }
        )
    }


def fake_read_single_time(fnames, metadata_only=False, chans=None, **kwargs):
    """Mimic a reader's `call_single_time`, failing based on the filename.

    Only single-file calls raise. After the per-file loop, files sharing a scan
    time are read again as a group, and a recoverable file only succeeds when
    grouped with a good one (as with the real seviri_hrit reader).
    """
    if len(fnames) > 1:
        return _good_metadata(fnames)
    fname = fnames[0]
    if "novalid" in fname:
        raise NoValidFilesError("No valid files")
    if "value" in fname:
        raise ValueError("No requested channels in file")
    if "hritbad" in fname:
        raise HritError("Unable to read image data")
    if "hritok" in fname:
        raise HritError(
            "Unknown projection encountered",
            start_datetime=START_TIME,
            end_datetime=START_TIME,
        )
    return _good_metadata(fnames)


def _reader_records(caplog, level):
    """Return log messages emitted by the readers interface at `level`."""
    return [
        rec.getMessage()
        for rec in caplog.records
        if rec.name == READERS_LOGGER and rec.levelno == level
    ]


def test_mixed_files_logs_each_exclusion_and_one_warning(caplog):
    """Excluded files are logged at INFO, with one aggregated WARNING."""
    caplog.set_level(logging.INFO, logger=READERS_LOGGER)
    fnames = [
        f"{FAKE_DIR}/{name}.nc"
        for name in ["good", "novalid", "value", "hritbad", "hritok"]
    ]

    readers.read_data_to_xarray_dict(fnames, fake_read_single_time, metadata_only=True)

    info_messages = _reader_records(caplog, logging.INFO)
    for name, exc_name in [
        ("novalid.nc", "NoValidFilesError"),
        ("value.nc", "ValueError"),
        ("hritbad.nc", "HritError"),
    ]:
        assert any(name in msg and exc_name in msg for msg in info_messages)
    assert any("hritok.nc" in msg for msg in info_messages)
    assert not any(FAKE_DIR in msg for msg in info_messages)

    warning_messages = _reader_records(caplog, logging.WARNING)
    assert len(warning_messages) == 1
    assert "3 of 5" in warning_messages[0]

    # NoValidFilesError files are dropped; the rest stay aligned with None times.
    assert len(readers.start_times) == 4
    assert readers.start_times.count(START_TIME) == 2
    assert readers.start_times.count(None) == 2


def test_all_files_rejected_raises_with_capped_summary(caplog):
    """All-rejected input raises with a summary capped at five files."""
    caplog.set_level(logging.INFO, logger=READERS_LOGGER)
    fnames = [f"{FAKE_DIR}/value{idx}.nc" for idx in range(7)]

    with pytest.raises(NoValidFilesError) as excinfo:
        readers.read_data_to_xarray_dict(
            fnames, fake_read_single_time, metadata_only=True
        )

    err_msg = str(excinfo.value)
    assert "Excluded files:" in err_msg
    assert "ValueError" in err_msg
    assert "... and 2 more" in err_msg
    listed_files = [f"value{idx}.nc" for idx in range(7) if f"value{idx}.nc" in err_msg]
    assert len(listed_files) == 5

    warning_messages = _reader_records(caplog, logging.WARNING)
    assert len(warning_messages) == 1
    assert "7 of 7" in warning_messages[0]


def test_all_valid_files_emit_no_warning(caplog):
    """No WARNING is logged when every file is usable."""
    caplog.set_level(logging.INFO, logger=READERS_LOGGER)
    fnames = [f"{FAKE_DIR}/good{idx}.nc" for idx in range(2)]

    readers.read_data_to_xarray_dict(fnames, fake_read_single_time, metadata_only=True)

    assert _reader_records(caplog, logging.WARNING) == []


def test_hrit_error_carries_datetimes():
    """Check HritError keeps its datetimes, message, and args."""
    err = HritError("msg", start_datetime=START_TIME, end_datetime=START_TIME)
    assert err.start_datetime == START_TIME
    assert err.end_datetime == START_TIME
    assert str(err) == "msg"
    assert err.args == ("msg",)
    assert HritError("msg").start_datetime is None
