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

"""Test script for representative product comparisons."""

import logging

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
    from geoips.commandline.log_setup import log_with_emphasis

    out_difftxt = plugin.get_out_diff_fname(compare_product, output_product)
    diffout = []
    retval = True
    import xarray

    out_xobj = xarray.open_dataset(output_product)
    compare_xobj = xarray.open_dataset(compare_product)

    if out_xobj.attrs != compare_xobj.attrs:
        message = "BAD GeoIPS NetCDF file attributes do NOT match exactly"
        log_with_emphasis(LOG.interactive, message)
        log_with_emphasis(LOG.interactive, f"output_product: {output_product}")
        log_with_emphasis(LOG.interactive, f"compare_product: {compare_product}")
        LOG.interactive("    ****************************************************")
        LOG.interactive(
            "    *** BAD GeoIPS NetCDF file attributes do NOT match exactly ***"
        )
        LOG.interactive("    ***   output_product: %s ***", output_product)
        LOG.interactive("    ***   compare_product: %s ***", compare_product)
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
        LOG.interactive("    ****************************************************")
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
        log_with_emphasis(LOG.interactive, message)
        log_with_emphasis(LOG.interactive, f"output_product: {output_product}")
        log_with_emphasis(LOG.interactive, f"compare_product: {compare_product}")
        LOG.interactive("    ****************************************************")
        LOG.interactive(
            "    *** BAD GeoIPS NetCDF files do not match within tolerance *****"
        )
        LOG.interactive("    ***   output_product: %s ***", output_product)
        LOG.interactive("    ***   compare_product: %s ***", compare_product)
        for line in str(resp).split("\n"):
            LOG.interactive(f"    *** {line} ***")
        diffout += [
            "\nxarray objects do not match between current output and comparison\n"
        ]
        diffout += [f"\nOut: {out_xobj}\n"]
        diffout += [f"\nCompare: {compare_xobj}\n"]
        diffout += [f"\n{resp}\n"]
        for varname in compare_xobj.variables:
            maxdiff = (compare_xobj[varname] - out_xobj[varname]).max()
            mindiff = (compare_xobj[varname] - out_xobj[varname]).min()
            meandiff = (compare_xobj[varname] - out_xobj[varname]).mean()
            if mindiff != 0:
                LOG.interactive(f"    *** mindiff {varname}: {mindiff} ***")
                diffout += [f"mindiff {varname}: {mindiff}\n"]
            if maxdiff != 0:
                LOG.interactive(f"    *** maxdiff {varname}: {maxdiff} ***")
                diffout += [f"maxdiff {varname}: {maxdiff}\n"]
            if meandiff != 0:
                LOG.interactive(f"    *** meandiff {varname}: {meandiff} ***")
                diffout += [f"meandiff {varname}: {meandiff}\n"]
        LOG.info("    " + "*" * 64)
        retval = False

    try:
        xarray.testing.assert_identical(compare_xobj, out_xobj)
    except AssertionError as resp:
        log_with_emphasis(LOG.info, "INFORMATIONAL ONLY assert_identical differences")
        for line in str(resp).split("\n"):
            LOG.info(f"    *** {line} ***")
        for varname in compare_xobj.variables:
            maxdiff = (compare_xobj[varname] - out_xobj[varname]).max()
            mindiff = (compare_xobj[varname] - out_xobj[varname]).min()
            meandiff = (compare_xobj[varname] - out_xobj[varname]).mean()
            if mindiff != 0:
                LOG.info(f"    *** mindiff {varname}: {mindiff} ***")
            if maxdiff != 0:
                LOG.info(f"    *** maxdiff {varname}: {maxdiff} ***")
            if meandiff != 0:
                LOG.info(f"    *** meandiff {varname}: {meandiff} ***")
        LOG.info("    " + "*" * 64)

    if retval is False:
        with open(out_difftxt, "w") as fobj:
            fobj.writelines(diffout)
        return False

    return True


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
