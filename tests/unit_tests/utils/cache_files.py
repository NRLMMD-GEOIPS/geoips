"""Unit tests for geoips.utils.cache_files."""

import os
import shutil
import yaml
import json
import tempfile

from geoips.utils.cache_files import (
    source_modified,
    create_cached_json_from_yaml,
    get_cached_json,
)


def test_source_modified():
    """Test the source_modified function.

    Create a temporary source and destination file, then test that source_modified
    returns True if the source file is newer than the destination file, and False
    otherwise. This will also test the case where the destination file does not exist.
    """
    tmp_dir = tempfile.mkdtemp()
    cache_dir = tempfile.mkdtemp()

    # Create a temporary source and destination file
    source = f"{tmp_dir}/geoips_test_source.txt"
    dest = f"{cache_dir}/test_dest.txt"

    with open(source, "w") as f:
        f.write("This is a test.")

    # Test that source_modified returns True if the destination file does not exist.
    assert source_modified(source, dest)

    os.makedirs(cache_dir, exist_ok=True)
    with open(dest, "w") as f:
        f.write("This is a test.")

    # Test that source_modified returns True if the source file is newer
    os.utime(source, (os.path.getatime(source), os.path.getmtime(source) + 1))
    assert source_modified(source, dest)

    # Test that source_modified returns False if the destination file is newer
    os.utime(dest, (os.path.getatime(dest), os.path.getmtime(dest) + 1))
    assert not source_modified(source, dest)

    # Clean up
    os.remove(source)
    os.remove(dest)
    os.rmdir(cache_dir)
    os.rmdir(tmp_dir)


def test_create_cached_json_from_yaml():
    """Test the create_cached_json_from_yaml function.

    This will create a temporary YAML file, then call create_cached_json_from_yaml on
    it. This will read the YAML file write the data to a JSON file in `cache_dir`. The
    test just ensures that the JSON file was created and contains the correct data.
    """
    tmp_dir = tempfile.mkdtemp()
    cache_dir = tempfile.mkdtemp()

    # Create a temporary YAML file
    yaml_file = f"{tmp_dir}/test.yaml"
    with open(yaml_file, "w") as f:
        yaml.dump({"key": "value"}, f)

    # Create the cached JSON file
    json_file = create_cached_json_from_yaml(yaml_file, cache_dir=cache_dir)

    # Check that the JSON file was created and contains the correct data
    assert os.path.exists(json_file)
    with open(json_file, "r") as f:
        data = json.load(f)
        assert data == {"key": "value"}

    # Clean up
    os.remove(yaml_file)
    os.remove(json_file)
    os.rmdir(cache_dir)
    os.rmdir(tmp_dir)


def test_get_cached_json():
    """Test the get_cached_json function.

    Write a YAML file, then call get_cached_json on it. This will read the YAML file,
    write it to a JSON file in `cache_dir`, read the JSON file and return the data, then
    compare the new data to the original YAML data.
    """
    tmp_dir = tempfile.mkdtemp()
    cache_dir = tempfile.mkdtemp()

    # Create a temporary YAML file
    yaml_file = f"{tmp_dir}/test.yaml"
    with open(yaml_file, "w") as f:
        yaml.dump({"key": "value"}, f)

    # Get the cached JSON file
    data = get_cached_json(yaml_file, cache_dir=cache_dir)
    assert data == {"key": "value"}

    # Clean up
    os.remove(yaml_file)
    shutil.rmtree(cache_dir)
    os.rmdir(tmp_dir)
