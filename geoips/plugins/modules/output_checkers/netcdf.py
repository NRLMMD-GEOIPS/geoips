# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Test script for representative product comparisons."""

import logging

from geoips.commandline.log_setup import log_with_emphasis

LOG = logging.getLogger(__name__)

interface = "output_checkers"
family = "standard"
name = "netcdf"


def get_test_files(test_data_dir):
    """Return a Series of Netcdf paths, randomly modified from compare."""
    import xarray as xr
    import numpy as np
    from os import makedirs
    from os.path import exists, join

    savedir = join(test_data_dir, "scratch", "unit_tests", "test_netcdf")
    if not exists(savedir):
        makedirs(savedir)
    # Path for the "compare" NetCDF file
    compare_file = join(savedir, "compare.nc")

    # Generate random data for the "compare" file
    compare_data = np.random.rand(100, 100)
    compare_ds = xr.Dataset(data_vars={"data": (("x", "y"), compare_data)})
    compare_ds.to_netcdf(compare_file)

    # Paths for the other files
    matched_path = join(savedir, "matched.nc")
    close_mismatch_path = join(savedir, "close_mismatch.nc")
    bad_mismatch_path = join(savedir, "bad_mismatch.nc")

    # Randomly modify the "compare" data for "close_mismatch" and "bad_mismatch"
    close_mismatch_data = compare_data + np.random.normal(
        scale=0.05, size=compare_data.shape
    )
    bad_mismatch_data = compare_data + np.random.normal(
        scale=0.25, size=compare_data.shape
    )

    # Create DataArrays for the modified data
    close_mismatch_da = xr.DataArray(data=close_mismatch_data, dims=("x", "y"))
    bad_mismatch_da = xr.DataArray(data=bad_mismatch_data, dims=("x", "y"))

    # Create Datasets and save them to NetCDF files
    close_mismatch_ds = xr.Dataset(data_vars={"data": close_mismatch_da})
    bad_mismatch_ds = xr.Dataset(data_vars={"data": bad_mismatch_da})

    close_mismatch_ds.to_netcdf(close_mismatch_path)
    bad_mismatch_ds.to_netcdf(bad_mismatch_path)
    compare_ds.to_netcdf(matched_path)
    return compare_file, [matched_path, close_mismatch_path, bad_mismatch_path]


def perform_test_comparisons(plugin, compare_file, test_files):
    """Test the comparison of two Netcdf files with the Netcdf Output Checker."""
    for path_idx in range(len(test_files)):
        retval = plugin.module.outputs_match(
            plugin,
            test_files[path_idx],
            compare_file,
        )
        if path_idx == 0:
            assert retval is True
        else:
            assert retval is False


def correct_file_format(fname):
    """Check if fname is a geoips formatted netcdf file.

    Parameters
    ----------
    fname : str
        Name of file to check.

    Returns
    -------
    bool
        True if it is a geoips netcdf file, False otherwise.
    """
    import xarray

    try:
        xobj = xarray.open_dataset(fname)
    except Exception:
        return False
    from geoips.geoips_utils import get_required_geoips_xarray_attrs

    return set(get_required_geoips_xarray_attrs()).issubset(set(xobj.attrs.keys()))


def outputs_match(plugin, output_product, compare_product):
    """Check if two geoips formatted netcdf files match.

    Parameters
    ----------
    plugin: OutputCheckerPlugin
        The corresponding geotiff OutputCheckerPlugin that has access to needed methods
    output_product : str
        Full path to current output product
    compare_product : str
        Full path to comparison product

    Returns
    -------
    bool
        Return True if products match, False if they differ
    """
    out_difftxt = plugin.get_out_diff_fname(compare_product, output_product)
    diffout = []
    retval = True
    import xarray

    out_xobj = xarray.open_dataset(output_product)
    compare_xobj = xarray.open_dataset(compare_product)

    if out_xobj.attrs != compare_xobj.attrs:
        message = "BAD GeoIPS NetCDF file attributes do NOT match exactly"
        log_with_emphasis(
            LOG.interactive,
            message,
            f"output_product: {output_product}",
            f"compare_product: {compare_product}",
        )
        for attr in out_xobj.attrs.keys():
            if attr not in compare_xobj.attrs:
                diffstr = (
                    f"\nattr {attr}\n\n"
                    f"output\n{out_xobj.attrs[attr]}\n\n"
                    "not in comparison\n"
                )
                diffout += [diffstr]
                LOG.interactive(diffstr)
            elif out_xobj.attrs[attr] != compare_xobj.attrs[attr]:
                diffstr = (
                    f"\nattr {attr}\n\n"
                    f"output\n{out_xobj.attrs[attr]}\n\n"
                    f"comparison\n{compare_xobj.attrs[attr]}\n"
                )
                diffout += [diffstr]
                LOG.interactive(diffstr)
        for attr in compare_xobj.attrs.keys():
            if attr not in out_xobj.attrs:
                diffstr = (
                    f"\nattr {attr}\n\n"
                    f"not in output\n\n"
                    f"comparison\n{compare_xobj.attrs[attr]}\n"
                )
                diffout += [diffstr]
                LOG.interactive(diffstr)
            elif out_xobj.attrs[attr] != compare_xobj.attrs[attr]:
                diffstr = (
                    f"\nattr {attr}\n\n"
                    f"output\n{out_xobj.attrs[attr]}\n\n"
                    f"comparison\n{compare_xobj.attrs[attr]}\n"
                )
                diffout += [diffstr]
                LOG.interactive(diffstr)
        diffout += ["\n"]
        retval = False

    if retval is False:
        with open(out_difftxt, "w") as fobj:
            fobj.writelines(diffout)
        return False

    try:
        xarray.testing.assert_allclose(compare_xobj, out_xobj)
    except AssertionError as resp:
        message = "BAD GeoIPS NetCDF files do not match within tolerance"
        log_with_emphasis(
            LOG.interactive,
            message,
            f"output_product: {output_product}",
            f"compare_product: {compare_product}",
        )
        log_with_emphasis(LOG.interactive, *[line for line in str(resp).split("\n")])
        diffout += [
            "\nxarray objects do not match between current output and comparison\n"
        ]
        diffout += [f"\nOut: {out_xobj}\n"]
        diffout += [f"\nCompare: {compare_xobj}\n"]
        diffout += [f"\n{resp}\n"]
        for varname in compare_xobj.variables:
            logged_messages = log_object_diff_values(
                out_xobj, compare_xobj, varname, log_function=LOG.warning
            )
            diffout.extend([[m] for m in logged_messages])
        retval = False

    try:
        xarray.testing.assert_identical(compare_xobj, out_xobj)
    except AssertionError as resp:
        lines = ["INFORMATIONAL ONLY assert_identical differences"]
        for line in str(resp).split("\n"):
            lines += [line]
        for varname in compare_xobj.variables:
            log_object_diff_values(
                out_xobj, compare_xobj, varname, log_function=LOG.info
            )
        log_with_emphasis(LOG.info, *lines)

    if retval is False:
        with open(out_difftxt, "w") as fobj:
            fobj.writelines(diffout)
        return False

    return True


def log_object_diff_values(object1, object2, compare_key, log_function=LOG.info):
    r"""
    Log differences two objects via key and returns messages detailing differences.

    Computes the maximum, minimum, and mean differences for the values associated
    with a specified key in two objects. Generates messages for any non-zero
    differences and logs these messages. The messages are also returned as a list
    of strings for further use. Takes in an optional custom logging function,
    defaults to info logging.

    Objects must expose a min, max, and mean function after the difference
    between them is computed.

    Parameters
    ----------
    object1 : object
        The first object containing the key for comparison. Must support
        subscripting with the compare key and arithmetic operations.
    object2 : object
        The second object for comparison. Must also support subscripting with the
        compare key and arithmetic operations.
    compare_key : str
        The key for the values to be compared between `object1` and `object2`.
    log_func : func, optional
        The function to be used for logging, must take in a list of strings of min
        length 0.

    Returns
    -------
    messages : list of str
        A list of messages indicating non-zero min, max, and mean differences for
        the values associated with `compare_key`, formatted as strings.

    Notes
    -----
    Only logs and returns messages for non-zero differences. If there are no non-zero
    differences, an empty list is returned.

    Uses `log_with_emphasis` to log the messages.

    Examples
    --------
    Given two objects `obj1` and `obj2` with a key `temp`:

    >>> obj1 = {'temp': np.array([1, 2, 3])}
    >>> obj2 = {'temp': np.array([2, 3, 4])}
    >>> log_object_diff_values(obj1, obj2, 'temp')
    ['mindiff temp: -1\\n', 'maxdiff temp: -1\\n', 'meandiff temp: -1.0\\n']

    This will log and return messages about differences in `temp` values.
    """
    maxdiff = (object2[compare_key] - object1[compare_key]).max()
    mindiff = (object2[compare_key] - object1[compare_key]).min()
    meandiff = (object2[compare_key] - object1[compare_key]).mean()
    messages = [
        f"mindiff {compare_key}: {mindiff}\n",
        f"maxdiff {compare_key}: {maxdiff}\n",
        f"meandiff {compare_key}: {meandiff}\n",
    ]
    log_with_emphasis(log_function, *messages)
    return messages


def call(plugin, compare_path, output_products):
    """Compare the "correct" netcdfs found the list of current output_products.

    Compares files produced in the current processing run with the list of
    "correct" files contained in "compare_path".

    Parameters
    ----------
    plugin: OutputCheckerPlugin
        The corresponding netcdf OutputCheckerPlugin that has access to needed methods
    compare_path : str
        Path to directory of "correct" products - filenames must match output_products
    output_products : list of str
        List of strings of current output products,
        to compare with products in compare_path

    Returns
    -------
    int
        Binary code: 0 if all comparisons were completed successfully.
    """
    retval = plugin.compare_outputs(
        compare_path,
        output_products,
    )
    return retval
