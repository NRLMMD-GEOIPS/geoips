# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Output Checkers interface module."""

from geoips.interfaces.base import (
    BaseModuleInterface,
    BaseModulePlugin,
    ValidationError,
)
import logging

# import subprocess
from geoips.commandline.log_setup import log_with_emphasis
import gzip
from glob import glob
from os.path import exists, splitext, basename, dirname, isdir, join
from os import makedirs, getenv
from shutil import copyfileobj
from geoips.filenames.base_paths import make_dirs


LOG = logging.getLogger(__name__)
rezip = False


def write_bad_comparisons_to_file(badcomps, compare_products, compare_strings, diffdir):
    """Write text file with cp commands to update products with bad comparisons.

    Write a text file that can be sourced to replace test output comparison files
    with the most recent outputs when the output checker returns a bad comparisons.

    When GeoIPS is updated in a way that changes the imagery and those changes
    are expected, the integration test image comparisons will fail. This
    function writes a file named `cp_BADCOMPARES.txt` which can be
    sourced to copy the new comparison files into place, overwriting
    the previous comparison files. This allows easily updating the test
    comparison outputs when code updates make expected changes to the
    output imagery.

    We must ensure we also gzip the comparison product in the test outputs
    directory after copying if the original test comparison output file was
    gzipped.  If applicable, a gzip command will also be added to
    cp_BADCOMPARES.txt.

    Parameters
    ----------
    badcomps: list
        List of files that returned a "BAD COMPARISON" from the output checker.
        These are the full paths to the files produced during the most recent
        run.
    compare_products: dict
        dictionary of comparison products - including the original comparison
        product file name, the gunzipped product file path if applicable,
        and the path to the file that should be used for comparison against
        "badcomps" files.
    compare_strings : list of str
        List of all comparison "tags" included in goodcomps and badcomps lists.

        * This list is used to remove the comparison tags from goodcomps and
          badcomps to retrieve only the file path.
    diffdir: str
        Full path to write "cp_BADCOMPARES.txt" file.
        NOTE: diffdir currently also is used to specify the path to the
        output files. Eventually we should pass in 2 separate paths, one
        to specify where to write the diff files, and a separate path
        indicating where to write the updated test output comparison files.

    Returns
    -------
    int
        Binary code: 0 if all comparisons were completed successfully, non-zero
        if there were bad comparisons.
    """
    for badcompare in badcomps:
        LOG.warning("BADCOMPARE %s", badcompare)
    if len(badcomps) > 0:
        fname_cp = join(diffdir, "cp_BADCOMPARES.txt")
        fname_badcptest = join(diffdir, "cptest_BADCOMPARES.txt")
        LOG.interactive(
            "BADCOMPARES Commands to copy %d files that had bad comparisons",
            len(badcomps),
        )
        LOG.debug(f"  source {fname_badcptest}")
        LOG.interactive(f"  source {fname_cp}")
        # Include print statement for easy copy/paste at the command line
        print(f"***\nsource {fname_cp}\n***")
        comparison_path = join(diffdir, "..")
        test_path = join(diffdir, "BADCOMPARES")
        with open(fname_cp, "a") as fobj:
            for badcomp in badcomps:
                if compare_strings is not None:
                    for compare_string in compare_strings:
                        badcomp = badcomp.replace(compare_string, "")
                fobj.write(f"cp -v {badcomp} {comparison_path}\n")
                comparison_basename = basename(badcomp)
                comparison_filename = join(comparison_path, comparison_basename)
                comparison_gz_filename = comparison_filename + ".gz"
                if (
                    basename(comparison_gz_filename) in compare_products
                    and compare_products[basename(comparison_gz_filename)][
                        "gunzipped_comparison"
                    ]
                ):
                    fobj.write(f"gzip {comparison_filename}\n")
        with open(fname_badcptest, "a") as fobj:
            fobj.write(f"mkdir {test_path}\n")
            for badcomp in badcomps:
                badcomp = badcomp.replace("IMAGE ", "")
                badcomp = badcomp.replace("TEXT ", "")
                badcomp = badcomp.replace("GEOIPS NETCDF ", "")
                badcomp = badcomp.replace("GEOTIFF ", "")
                # For display purposes - tifs are easier to view
                test_basename = basename(badcomp).replace(".jif", ".tif")
                test_filename = join(test_path, test_basename)
                fobj.write(f"cp {badcomp} {test_filename}\n")
    # Assemble the return value and return.
    # Bad comparisons are bits 0/1 of the return code.
    retval = 0
    if len(badcomps) != 0:
        retval = len(badcomps)
        if len(badcomps) > 4:
            retval = 4
        LOG.info("BADCOMPS %s", len(badcomps))
    return retval << 0


def write_remove_temp_files_to_file(remove_temp_files, diffdir):
    """Write text file with rm commands to remove temporary files.

    Write a text file ``rm_TEMPFILES.txt`` that can be sourced to remove
    temporary files that were created in the ``$GEOIPS_OUTDIRS`` scratch
    directory during the output comparison checks during integration tests.
    This currently includes temporary gunzipped versions of products
    (ie, if a product was gzipped during processing, then gunzipped to
    a temporary location during the comparison tests, it will get added
    to the `remove_temp_files` list), and may include additional temporary
    files in the future.

    The gunzipped files are not auto-deleted during the comparison process,
    because they must be manually copied to the tets outputs directory after
    processing is complete, so we do not remove the files at runtime.

    Parameters
    ----------
    remove_temp_files: list
        List of files that should be written to ``rm_TEMPFILES.txt`` for deletion.
        This currently includes auto-gunzipped products, and potentially
        additional temporary files in the future.
    diffdir: str
        Full path to write ``rm_TEMPFILES.txt`` file
        NOTE: `diffdir` currently also is used to specify the path to the
        output files. Eventually we should pass in 2 separate paths, one
        to specify where to write the diff files, and a separate path
        indicating where to write the updated test output comparison files.

    Returns
    -------
    int
        Binary code: 0 for successfully written ``rm_TEMPFILES.txt`` file.
    """
    if len(remove_temp_files) > 0:
        fname_rmtemp = join(diffdir, "rm_TEMPFILES.txt")
        LOG.interactive(
            "RMTEMPFILES Commands to remove %d "
            "temp files from gunzipped files scratch path.",
            len(remove_temp_files),
        )
        LOG.interactive(f"  source {fname_rmtemp}")
        # Include print statement for easy copy/paste at the command line
        print(f"***\nsource {fname_rmtemp}\n***")
        with open(fname_rmtemp, "a") as fobj:
            for remove_temp_file in remove_temp_files:
                fobj.write(f"rm -v {remove_temp_file}\n")
    return 0


def write_missing_products_to_file(missingproducts, compare_products, diffdir):
    """Write text file with rm commands to remove products from comparison directory.

    Write a text file contatining rm commands that can be sourced to remove
    existing test output comparison files from the test comparison directories
    that were NOT found in the most recent output.

    When GeoIPS is updated in a way that intentionally causes a previously
    expected output to no longer be produced, it will cause the integration
    test comparison to fail with a MISSING PRODUCT error (ie, a file
    exists in the test comparison directory, but is not a current output
    product).

    When this is intended behaviour due to recent code updates, we must
    remove that product from the test output comparison directories.

    This function writes a file named `rm_MISSINGPRODUCTS.txt` which
    can be sourced to remove the files from the test comparison directory
    that were NOT found in the list of current output products. This
    allows easily updating the test comparison outputs when code updates
    make expected changes to the output products.

    Parameters
    ----------
    missingproducts: list
        List of files that returned a "MISSING PRODUCT" from the output checker.
        These are the full paths to the files produced during the most recent
        run.
    compare_products: dict
        dictionary of comparison products - including the original comparison
        product file name, the gunzipped product file path if applicable,
        and the path to the file that should be used for comparison against
        "missingproducts" files.
    diffdir: str
        Full path to write "rm_MISSINGPRODUCTS.txt" file
        NOTE: diffdir currently also is used to specify the path to the
        output files. Eventually we should pass in 2 separate paths, one
        to specify where to write the diff files, and a separate path
        indicating where to write the updated test output comparison files.

    Returns
    -------
    int
        Binary code: 0 if all comparisons were completed successfully, non-zero
        if there were missing products.
    """
    # This should be in loop below
    # for compareproduct in compare_products:
    #     LOG.warning(
    #         "MISSINGPRODUCT not in current run: %s",
    #         basename(compareproduct),
    #     )
    # If we have any missingproducts, loop through in order to write them to
    # file for manual removal from the test comparison directories.
    if len(missingproducts) > 0:
        # Actual rm commands to remove files
        fname_rm = join(diffdir, "rm_MISSINGPRODUCTS.txt")
        # cp commands to copy over the products for review to a temporary
        # directory.  This does not impact the actual test outputs.
        fname_missingprodcptest = join(diffdir, "cptest_MISSINGPRODUCTS.txt")
        LOG.interactive(
            "MISSINGPRODUCTS Commands to remove %d "
            "incorrect files from test output path.",
            len(missingproducts),
        )
        LOG.debug("  source {0}".format(fname_missingprodcptest))
        # If there are missing products, ensure the source command to
        # remove them from the comparison test outputs directory is
        # printed at the interactive log level
        LOG.interactive("  source {0}".format(fname_rm))
        # Include print statement for easy copy/paste at the command line
        print("***\nsource {0}\n***".format(fname_rm))
        test_path = join(diffdir, "MISSINGPRODUCTS")
        with open(fname_rm, "a") as fobj:
            # Now loop through each missing product to write them to the file
            for missingproduct in missingproducts:
                missingproduct_basename = basename(missingproduct)
                for compare_product in compare_products:
                    # Pull the file that is actually used for comparison from
                    # the compare_products dictionary.
                    file_for_comparison = compare_products[compare_product][
                        "file_for_comparison"
                    ]
                    file_for_comparison_basename = basename(file_for_comparison)
                    # If the basename of the current missing product matches the
                    # basename of the file for comparison, then write out the
                    # command to remove the actual stored comparison file from
                    # the test repo.
                    if missingproduct_basename == file_for_comparison_basename:
                        comparison_filename = compare_products[compare_product][
                            "stored_comparison"
                        ]
                        fobj.write(f"  rm -v {comparison_filename}\n")
                        LOG.debug(f"    TEST OUTPUT: {comparison_filename}")
                        LOG.warning(
                            "MISSINGPRODUCT not in current run: %s",
                            basename(comparison_filename),
                        )
                    else:
                        comparison_filename = compare_products[compare_product][
                            "stored_comparison"
                        ]
                        fobj.write(f"  rm -v {comparison_filename}\n")
                        LOG.debug(f"    TEST OUTPUT: {file_for_comparison}")
                        LOG.warning(
                            "MISSINGPRODUCT not in current run: %s",
                            basename(comparison_filename),
                        )
        # This is just for testing purposes - write out copy commands to
        # copy the missing product into a test location for easy review.
        with open(fname_missingprodcptest, "a") as fobj:
            fobj.write(f"mkdir {test_path}\n")
            for missingproduct in missingproducts:
                # For display purposes - tifs are easier to view
                test_basename = basename(missingproduct).replace(".jif", ".tif")
                test_filename = join(test_path, test_basename)
                fobj.write(f"cp -v {missingproduct} {test_filename}\n")
    # Assemble the return value and return.
    # Missing products are bits 4/5 of the return code.
    retval = 0
    if len(missingproducts) != 0:
        retval = len(missingproducts)
        if len(missingproducts) > 4:
            retval = 4
        LOG.info("MISSINGPRODUCTS %s", len(missingproducts))
    return retval << 4


def write_missing_comparisons_to_file(missingcomps, diffdir):
    """Write text file with cp commands to add products to comparison directory.

    Write a text file contatining cp commands that can be sourced to add
    new test output comparison files to the test comparison directories
    that were found in the most recent output and were not previously in
    the test comparison directory.

    When GeoIPS is updated in a way that intentionally causes a new
    output product, it will cause the integration test comparison to fail
    with a MISSING COMPARE error (ie, a file exists in the current output
    product path, but does not exist in the test comparison directory).

    When this is intended behaviour due to recent code updates, we must
    add that new product to the test output comparison directories from
    the current output path.

    This function writes a file named `cp_MISSINGCOMPARE.txt` which
    can be sourced to copy the appropriate files from the current
    output product path into the test comparison directory. This
    allows easily updating the test comparison outputs when code updates
    make expected changes to the output products.

    Parameters
    ----------
    missingcomps: list
        List of files that returned a "MISSING COMPARE" from the output checker.
        These are the full paths to the files produced during the most recent
        run.
    diffdir: str
        Full path to write "rm_MISSINGCOMPARE.txt" file
        NOTE: diffdir currently also is used to specify the path to the
        output files. Eventually we should pass in 2 separate paths, one
        to specify where to write the diff files, and a separate path
        indicating where to write the updated test output comparison files.

    Returns
    -------
    int
        Binary code: 0 if all comparisons were completed successfully, non-zero
        if there were missing comparisons.
    """
    for missingcompare in missingcomps:
        LOG.warning("MISSINGCOMPARE not in comparepath: %s", basename(missingcompare))
    if len(missingcomps) > 0:
        fname_cp = join(diffdir, "cp_MISSINGCOMPARE.txt")
        fname_missingcompcptest = join(diffdir, "cptest_MISSINGCOMPARE.txt")
        LOG.interactive(
            "MISSINGCOMPARE Commands to copy %d missing files to comparison path.",
            len(missingcomps),
        )
        LOG.debug("  source {0}".format(fname_missingcompcptest))
        LOG.interactive("  source {0}".format(fname_cp))
        # Include print statement for easy copy/paste at the command line
        print("***\nsource {0}\n***".format(fname_cp))
        comparison_path = join(diffdir, "..")
        test_path = join(diffdir, "MISSINGCOMPARE")
        with open(fname_cp, "a") as fobj:
            for missingcomp in missingcomps:
                # We are passing the missingcomp directly to the diff dir
                # We have no knowledge if these should be gzipped or not,
                # so they are just copied as is.  Developers must manually
                # gzip before commiting if desired.
                fobj.write(f"  cp -v {missingcomp} {comparison_path}\n")
                LOG.debug(f"    CURR OUTPUT: {missingcomp}")
        with open(fname_missingcompcptest, "a") as fobj:
            fobj.write(f"mkdir {test_path}\n")
            for missingcomp in missingcomps:
                # For display purposes - tifs are easier to view
                test_basename = basename(missingcomp).replace(".jif", ".tif")
                test_filename = join(test_path, test_basename)
                fobj.write(f"cp -v {missingcomp} {test_filename}\n")
    # Assemble the return value and return.
    # Missing comparisons are bits 2/3 of the return code.
    retval = 0
    if len(missingcomps) != 0:
        retval = len(missingcomps)
        if len(missingcomps) > 4:
            retval = 4
        LOG.info("MISSINGCOMPS %s", len(missingcomps))
    return retval << 0


def write_good_comparisons_to_file(goodcomps, compare_strings, diffdir):
    """Write all good comparisons to a file for easy collection of outputs.

    During integration tests, if the current product output matches the
    test output stored in the test comparison directories, the output
    checkers will return 0 as a GOOD COMPARE.  These outputs do not need
    to be updated in the test comparison directories, since the current
    products and test comparison outputs match within tolerance.

    The developer may desire copying these files to a single location
    convenience, however.

    This function writes a file named `cptest_GOODCOMPARE.txt` which
    can be sourced to copy all products that were identical to the
    current output products to a common location, for convenience.
    This does not impact any files stored in the test comparison
    directories.

    Parameters
    ----------
    goodcomps: list
        List of files that returned a "GOOD COMPARE" from the output checker.
        These are the full paths to the files produced during the most recent
        run.
    compare_strings : list of str
        List of all comparison "tags" included in goodcomps and badcomps lists.

        * This list is used to remove the comparison tags from goodcomps and
          badcomps to retrieve only the file path when writing the cp commands.
    diffdir: str
        Full path to write "cptest_GOODCOMPARE.txt" file
        NOTE: diffdir currently also is used to specify the path to the
        output files. Eventually we should pass in 2 separate paths, one
        to specify where to write the diff files, and a separate path
        indicating where to write the updated test output comparison files.

    Returns
    -------
    int
        Binary code: 0 for good comparisons
    """
    for goodcompare in goodcomps:
        LOG.warning("GOODCOMPARE %s", goodcompare)
    if len(goodcomps) > 0:
        fname_goodcptest = join(diffdir, "cptest_GOODCOMPARE.txt")
        LOG.debug(f"source {fname_goodcptest}")
        test_path = join(diffdir, "GOODCOMPARE")
        with open(fname_goodcptest, "a") as fobj:
            fobj.write(f"mkdir {test_path}\n")
            for goodcomp in goodcomps:
                if compare_strings is not None:
                    for compare_string in compare_strings:
                        goodcomp = goodcomp.replace(compare_string, "")
                # For display purposes - tifs are easier to view
                test_basename = basename(goodcomp).replace(".jif", ".tif")
                test_filename = join(test_path, test_basename)
                fobj.write(f"cp {goodcomp} {test_filename}\n")
    return 0


def get_missing_products(output_products_for_comparison, compare_products):
    """Get list of missing products from compare_products_dictionary.

    Parameters
    ----------
    output_products_for_comparison: list
        List of output products from the current run.
    compare_products: dict
        Dictionary of products found in the test comparison directory.
        Note the key of the compare_products dictionary is the filename that
        is stored in the comparison directory (ie, this may be a gzipped file).
        We must use the "gunzipped_comparison", "stored_comparison", and
        "file_for_comparison" keys within that dictionary to ensure we are
        accessing the correct versions of the files.

    Returns
    -------
    missingproducts : list
        List of products that were missing from the current run.
    """
    missingproducts = []
    for output_product_for_comparison in output_products_for_comparison:
        found_one = False
        # compare_products is a dictionary,
        # with "basename(compare_product)" as the keys.
        # Add the full paths to the missing files as the missingproducts.
        for basename_compare_product in compare_products:
            # We want to check that file_for_comparison is in the list of
            # output_products_for_comparison.  We know file_for_comparison will always
            # be the file corresponding to the actual current output products.
            # gunzipped_comparisons may be None, and stored_comparisons may be
            # gzipped.
            file_for_comparison = compare_products[basename_compare_product][
                "file_for_comparison"
            ]
            if basename(file_for_comparison) == basename(output_product_for_comparison):
                found_one = True
        if not found_one:
            missingproducts += [output_product_for_comparison]
    return missingproducts


def is_gz(fname):
    """Check if fname is a gzip file.

    Parameters
    ----------
    fname : str
        Name of file to check.

    Returns
    -------
    bool
        True if it is a gz file, False otherwise.
    """
    if splitext(fname)[-1] in [".gz"]:
        return True
    # If a file exists with the base fname appended with .gz,
    # then use that.
    if glob(fname + ".gz"):
        return True
    return False


def gunzip_product(fname, is_comparison_product=False, clobber=False):
    """Gunzip file fname.

    Parameters
    ----------
    fname : str
        File to gunzip.
    is_comparison_product : bool, default False
        * If True, set to $GEOIPS_OUTDIRS/gunzipped_products/comparison_products
        * If False, set to $GEOIPS_OUTDIRS/gunzipped_products/output_products
    clobber : bool, default False
        If True, overwrite existing file, else do nothing.

    Returns
    -------
    str
        Filename after gunzipping
    """
    # If it is already a .gz file, use that.
    if splitext(fname)[-1] in [".gz"]:
        gz_fname = fname
    # Otherwise, see if the .gz version exists.
    elif glob(fname + ".gz"):
        gz_fname = fname + ".gz"

    messages = ["Gunzipping product for comparisons"]
    messages.append(f"gunzip {gz_fname}")
    log_with_emphasis(LOG.info, *messages)

    if is_comparison_product:
        save_dir = join(
            getenv("GEOIPS_OUTDIRS"),
            "scratch",
            "gunzipped_products",
            "comparison_products",
        )
    else:
        save_dir = join(
            getenv("GEOIPS_OUTDIRS"), "scratch", "gunzipped_products", "output_products"
        )
    make_dirs(save_dir)
    gunzip_basename = str(basename(gz_fname)).replace(".gz", "")
    gunzip_filename = join(save_dir, gunzip_basename)
    if clobber or not exists(gunzip_filename):
        LOG.interactive("Gunzipping file %s to %s", gz_fname, save_dir)
        # Read in the compressed data
        with gzip.open(gz_fname, "rb") as f_in:
            with open(gunzip_filename, "wb") as f_out:
                copyfileobj(f_in, f_out)
    return gunzip_filename


class OutputCheckersBasePlugin(BaseModulePlugin):
    """Output Checkers Base Plugin for comparing data outputs."""

    def is_gz(self, fname):
        """Check if fname is a gzip file.

        Parameters
        ----------
        fname : str
            Name of file to check.

        Returns
        -------
        bool
            True if it is a gz file, False otherwise.
        """
        return is_gz(fname)

    def gunzip_product(self, fname, is_comparison_product=False, clobber=False):
        """Gunzip file fname.

        Parameters
        ----------
        fname : str
            File to gunzip.
        is_comparison_product : bool, default False
            * If True, set to $GEOIPS_OUTDIRS/gunzipped_products/comparison_products
            * If False, set to $GEOIPS_OUTDIRS/gunzipped_products/output_products
        clobber : bool, default False
            If True, overwrite existing file, else do nothing.

        Returns
        -------
        str
            Filename after gunzipping
        """
        return gunzip_product(fname, is_comparison_product, clobber)

    def get_out_diff_fname(self, compare_product, output_product, ext=None, flag=None):
        """Obtain the filename for output and comparison product diff.

        Parameters
        ----------
        compare_product : str
            Full path to product filename in the comparison directory
        output_product : str
            Full path to product filename in the current output directory
        ext : str, default=None
            Extension to use as an alternative to the original file extension
        flag : str, default=None
            Additional identifying string to include in output diff filename

        Returns
        -------
        out_diff_fname : str
            Full path to output diff file.
        """
        if not flag:
            flag = ""
        diffdir = join(
            dirname(compare_product), "diff_test_output_dir_{0}".format(getenv("USER"))
        )
        out_diff_fname = join(
            diffdir, "diff_test_output_" + flag + basename(output_product)
        )
        if not exists(diffdir):
            makedirs(diffdir)
        # Allow outputing a different extension than the original.
        if ext is not None:
            out_diff_fname = splitext(out_diff_fname)[0] + ext
        # Create a png diff image for simplicity
        elif splitext(out_diff_fname)[-1] == ".jif":
            out_diff_fname = splitext(out_diff_fname)[0] + ".png"
        return out_diff_fname

    def get_compare_products(self, compare_path):
        """Get dictionary of compare products from the compare_path.

        Parameters
        ----------
        compare_path: str
            Full path to the comparison directory to populate compare_products
            dictionary.

        Returns
        -------
        compare_products: dict
            Dictionary of products found in the test comparison directory.
            The key of the compare_products dictionary is the filename that
            is stored in the comparison directory (ie, this may be a gzipped file).

            * stored_comparison is the actual name stored in the comparison test dir
            * gunzipped comparison is the gunzipped version of the file, or None if
              file was not gzipped
            * file_for_comparison is "compare_product" if the file is not gzipped,
              and "gunzipped_comparison" if file is gzipped.
        remove_temp_files: list
            List of full paths to files that must be removed after processing
            (gunzipped files in GEOIPS_OUTDIRS scratch directory)
        """
        # Here we are collecting the basenames of the files for comparison, as
        # well as the associated gz filename if the original comparison product
        # was gzipped.
        compare_products = {}
        remove_temp_files = []
        # Loop through all comparison products found in "compare_path". We want
        # to collect ALL products available for comparison.
        for compare_product in glob(compare_path + "/*"):
            if isdir(compare_product):
                # Skip 'diff' output directory
                continue
            file_for_comparison = compare_product
            compare_product_gunzipped = None
            # If the current product is gzipped, we want to gunzip it for comparison.
            # We always gunzip for comparison.
            if self.is_gz(compare_product):
                # self.gunzip_product returns the resulting filename (which may be
                # in a different directory). NOTE: this is the first time gunzip
                # is run on compare_products, so ensure we clobber what is there.
                compare_product_gunzipped = self.gunzip_product(
                    compare_product, is_comparison_product=True, clobber=True
                )
                remove_temp_files += [compare_product_gunzipped]
                file_for_comparison = compare_product_gunzipped
            # This is a complete list of all comparison products.
            # stored_comparison is the actual name stored in the comparison test dir
            # gunzipped comparison is the gunzipped version of the file, or None if
            #   file was not gzipped
            # file_for_comparison is "compare_product" if the file is not gzipped,
            #   and "gunzipped_comparison" if file is gzipped.
            compare_products[basename(compare_product)] = {
                "stored_comparison": compare_product,
                "gunzipped_comparison": compare_product_gunzipped,
                "file_for_comparison": file_for_comparison,
            }

        return compare_products, remove_temp_files

    def perform_comparisons(
        self,
        output_products,
        compare_products,
        **kwargs,
    ):
        """Get the final output products list from the original list of outputs.

        Parameters
        ----------
        output_products : list
            This is the original list of output products, exactly as they are
            produced during processing.  If a product is gzipped during processing,
            the output_products list will include the gzipped file.
        compare_products : dict
            This is a dictionary containing all of the comparison products available
            in the test outputs directory.

            * Keys: basename of actual output product as created during run
              (ie, gzipped if applicable)

              * key: "file_for_comparison", value: full path to file that is used
                when comparing against the current output (ie, could be temporary
                gunzip location).
              * key: "gunzipped_comparison", value: None if original output file was
                not gzipped, full path to gunzipped file if original output file
                was gzipped.
              * key: "stored_comparison", value: full path to file that is stored in
                the tests outputs location (ie, could be gzipped)
        kwargs : dict
            keyword arguments to pass directly through to test products function.

        Returns
        -------
        output_products_for_comparison : list
            List of full paths to files that will be used for comparisons.  Ie,
            if the output product was gzipped, this would be the full path to
            the gunzipped file in the temporary location.
        missingcomps : list
            List of full paths to files that were found in the current run, and NOT
            found in the comparison directory.
        goodcomps : list
            List of full paths to files that had good comparisons.
        badcomps : list
            List of full paths to files that had bad comparisons between the
            current output products and the test comparison outputs.
        compare_strings : list
            List of strings included in log output for each type of comparison.
        remove_temp_files : list
            List of full paths to files that should be removed from temporary scratch
            directory.
        """
        output_products_for_comparison = []
        remove_temp_files = []
        missingcomps = []
        goodcomps = []
        badcomps = []
        compare_strings = []

        for output_product in output_products:
            # Skip 'diff' output directory
            if isdir(output_product):
                continue

            output_product_for_comparison = output_product
            # Gunzip the output product if it is a gzipped file.
            # We will perform all comparisons on the gunzipped form.
            if is_gz(output_product):
                output_product_for_comparison = self.gunzip_product(
                    output_product, is_comparison_product=False
                )
                remove_temp_files += [output_product_for_comparison]

            log_with_emphasis(LOG.info, f"COMPARE {output_product_for_comparison}")
            found_one = False
            for compare_product in compare_products:
                file_for_comparison = compare_products[basename(compare_product)][
                    "file_for_comparison"
                ]
                # If the current output product matches the basename of the
                # gunzipped comparison product, then we have a match and
                # we can actually compare the files.  Whether a file is
                # gzipped in the current output directory, or the comparison
                # directory, we ALWAYS compare the gunzipped version, so this
                # comparison will always hold (output_product will always be
                # gunzipped, as well gunzipped_comparison).
                if basename(output_product_for_comparison) == basename(
                    file_for_comparison
                ):
                    found_one = True
                    test_product_func = self.test_products
                    goodcomps, badcomps, compare_strings = test_product_func(
                        output_product_for_comparison,
                        file_for_comparison,
                        goodcomps,
                        badcomps,
                        compare_strings,
                        **kwargs,
                    )
            # If we didn't find an exact filename match, then we have a missing
            # comparison, so append to the missingcomps list.
            if not found_one:
                missingcomps += [output_product_for_comparison]
            output_products_for_comparison += [output_product_for_comparison]

            LOG.info("")
        return (
            output_products_for_comparison,
            missingcomps,
            goodcomps,
            badcomps,
            compare_strings,
            remove_temp_files,
        )

    def compare_outputs(
        self,
        compare_path,
        output_products,
        **kwargs,
    ):
        """Compare the "correct" imagery found the list of current output_products.

        Compares files produced in the current processing run with the list of
        "correct" files contained in "compare_path".

        Parameters
        ----------
        compare_path : str
            Path to directory of "correct" products - filenames must match
            output_products
        output_products : list of str
            List of strings of current output products,
            to compare with products in compare_path
        kwargs: dict
            Dictionary containing kwargs for comparing products.
            This gets passed through to the "test_products" method.

        Returns
        -------
        int
            Binary code: 0 if all comparisons were completed successfully.
        """
        log_with_emphasis(LOG.info, f"COMPARISONS OF KNOWN OUTPUTS IN {compare_path}")
        # We gunzip comparison files to a temporary location, so keep track of
        # all the temporary files so we can remove them at the end.
        remove_temp_files = []

        compare_products, curr_remove_temp_files = self.get_compare_products(
            compare_path
        )
        remove_temp_files += curr_remove_temp_files

        # This returns the list of output products that will be used for
        # comparisons (ie, the gunzipped version if the original was gzipped),
        # the list of missing comparison products, and appends to the list
        # of temp files to remove.
        (
            output_products_for_comparison,
            missingcomps,
            goodcomps,
            badcomps,
            compare_strings,
            curr_remove_temp_files,
        ) = self.perform_comparisons(
            output_products,
            compare_products,
            **kwargs,
        )
        remove_temp_files += curr_remove_temp_files
        log_with_emphasis(
            LOG.info,
            f"DONE RUNNING COMPARISONS OF KNOWN OUTPUTS IN {compare_path}",
        )

        # Identify all missing products based on the list of output products
        # and the dictionary of comparison products
        missingproducts = get_missing_products(
            output_products_for_comparison, compare_products
        )

        diffdir = join(compare_path, f"diff_test_output_dir_{getenv('USER')}")
        if not exists(diffdir):
            makedirs(diffdir)

        retval = 0
        retval += write_good_comparisons_to_file(goodcomps, compare_strings, diffdir)
        retval += write_missing_comparisons_to_file(missingcomps, diffdir)
        retval += write_missing_products_to_file(
            missingproducts, compare_products, diffdir
        )
        retval += write_remove_temp_files_to_file(remove_temp_files, diffdir)
        retval += write_bad_comparisons_to_file(
            badcomps, compare_products, compare_strings, diffdir
        )

        LOG.info("retval: %s", bin(retval))
        if retval != 0:
            LOG.info(
                "Nonzero return value indicates error, 6 bit binary code: " "WXY where:"
            )
            LOG.info(
                (
                    "    Y (0-1): BADCOMP: number of bad comparisons found between"
                    "comparepath and current run output path"
                )
            )
            LOG.info(
                (
                    "    X (2-3): MISSINGCOMP: Number of products missing in "
                    "compare path but existing in current output path"
                )
            )
            LOG.info(
                (
                    "    W (4-5): MISSINGPROD: Number of products existing in "
                    "comparepath, but missing in current output path"
                )
            )

        return retval

    def test_products(
        self,
        output_product,
        compare_product,
        goodcomps,
        badcomps,
        compare_strings,
        **kwargs,
    ):
        """Test output_product against "good" product stored in "compare_path".

        Parameters
        ----------
        output_product : str
            * Full path to current output product
        compare_product : str
            * Full path to "good" comparison product
        goodcomps : list of str
            * List of full paths to all "good" successful comparisons
              (output and compare images match)
            * Each str is prepended with a "compare_string" tag to identify which
              comparison type was performed.
        badcomps : list of str
            * List of full paths to all "bad" unsuccessful comparisons
              (output and compare images differ)
            * Each str is prepended with a "compare_string" tag to identify which
              comparison type was performed.
        compare_strings : list of str
            * List of all comparison "tags" included in goodcomps and badcomps lists.
            * This list is used to remove the comparison tags from goodcomps and
              badcomps to retrieve only the file path.
        kwargs: dict
            Additional arguments to pass through to "outputs_match" method.

        Returns
        -------
        goodcomps: list of str
            All current good comparisons appended to the list passed in.
        badcomps: list of str
            All current bad comparisons appended to the list passed in.
        compare_strings: list of str
            All current comparison "tags" added to the list passed in.

        Raises
        ------
        TypeError
            Raised when current output product does not have an associated
            comparison test defined.
        """
        if self.is_gz(compare_product):
            compare_product = self.gunzip_product(
                compare_product, is_comparison_product=True
            )
        if self.name == "netcdf":
            comp_str = "GEOIPS NETCDF "
        else:
            comp_str = self.name.upper() + " "
        compare_strings += [comp_str]
        if self.module.outputs_match(
            self,
            output_product,
            compare_product,
            **kwargs,
        ):
            goodcomps += [comp_str + "{0}".format(output_product)]
        else:
            badcomps += [comp_str + "{0}".format(output_product)]

        return goodcomps, badcomps, compare_strings


class OutputCheckersInterface(BaseModuleInterface):
    """Output Checkers routines to apply when comparing data outputs."""

    name = "output_checkers"
    required_args = {"standard": {}}
    required_kwargs = {"standard": {}}
    plugin_class = OutputCheckersBasePlugin
    # required_args = {
    #     "standard": ["fname", "output_product", "compare_product"],
    #     "print_gunzip": ["fobj", "gunzip_fname"],
    #     "print_gzip": ["fobj", "gzip_fname"],
    # }
    # required_kwargs = {"standard": {}}
    # allowable_kwargs = {
    #     "test_product": ["goodcomps", "badcomps", "compare_strings"],
    #     "out_diffname": ["ext", "flag"],
    #     "compare_outputs": ["test_product_func"],
    # }

    def identify_checker(self, filename):
        """Identify the correct output checker plugin and return its name."""
        checker_found = False
        checker_name = None
        if is_gz(filename):
            # NOTE: this is the first time gunzip is run on the current
            # product, so ensure we clobber what is already there.
            filename = gunzip_product(
                filename, is_comparison_product=False, clobber=True
            )
        for output_checker in self.get_plugins():
            checker_found = output_checker.module.correct_file_format(filename)
            if checker_found:
                checker_name = output_checker.module.name
                break
        if not checker_found:
            raise TypeError("There isn't an output checker built for this data type.")
        return checker_name

    def get_plugin(self, name, rebuild_registries=None):
        """Return the output checker plugin corresponding to checker_name.

        Parameters
        ----------
        name : str
            - The name the desired plugin.
        rebuild_registries: bool (default=None)
            - Whether or not to rebuild the registries if get_plugin fails. If set to
              None, default to what we have set in geoips.filenames.base_paths, which
              defaults to True. If specified, use the input value of rebuild_registries,
              which should be a boolean value. If rebuild registries is true and
              get_plugin fails, rebuild the plugin registry, call then call
              get_plugin once more with rebuild_registries toggled off, so it only gets
              rebuilt once.
        """
        plug = super().get_plugin(name, rebuild_registries)
        if self.valid_plugin(plug):
            return plug

    def valid_plugin(self, plugin):
        """Check the validity of the supplied output_checker plugin."""
        if (
            not hasattr(plugin.module, "outputs_match")
            or not hasattr(plugin.module, "correct_file_format")
            or not hasattr(plugin.module, "call")
        ):
            raise ValidationError(
                "The plugin returned is missing one or more of the following functions."
                "\n[outputs_match, correct_file_format, call]. Please create those "
                "before using this plugin."
            )
        return True


output_checkers = OutputCheckersInterface()
