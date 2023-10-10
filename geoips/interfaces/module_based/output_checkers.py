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

"""Output Checkers interface module."""

from geoips.interfaces.base import (
    BaseModuleInterface,
    BaseModulePlugin,
    ValidationError,
)
import logging
from geoips.errors import PluginError
import subprocess
from os.path import exists, splitext, basename

LOG = logging.getLogger(__name__)
rezip = False


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
        if splitext(fname)[-1] in [".gz"]:
            return True
        return False

    def gunzip_product(self, fname):
        """Gunzip file fname.

        Parameters
        ----------
        fname : str
            File to gunzip.

        Returns
        -------
        str
            Filename after gunzipping
        """
        LOG.info("**** Gunzipping product for comparisons - will gzip after comparing")
        LOG.info("gunzip %s", fname)
        file_name = str(basename(fname)).replace(".gz", "")
        save_dir = "$GEOIPS_PACKAGES_DIR/outdirs/scratch/gunzipped_products/"
        subprocess.call(
            [
                "gunzip -c",
                fname,
                "> " + save_dir + file_name,
            ]
        )
        return save_dir + file_name

    def gzip_product(self, fname):
        """Gzip file fname.

        Parameters
        ----------
        fname : str
            File to gzip.

        Returns
        -------
        str
            Filename after gzipping
        """
        LOG.info("**** Gzipping product - leave things as we found them")
        LOG.info("gzip %s", fname)
        subprocess.call(["gzip", fname])
        return splitext(fname)[0]

    def print_gunzip_to_file(self, fobj, gunzip_fname):
        """Write the command to gunzip the passed "gunzip_fname" to file.

        Writes to the currently open file object, if required.
        """
        if exists(f"{gunzip_fname}.gz") and not exists(f"{gunzip_fname}"):
            fobj.write(f"gunzip -v {gunzip_fname}.gz\n")

    def print_gzip_to_file(self, fobj, gzip_fname):
        """Write the command to gzip the passed "gzip_fname" to file.

        Writes to the currently open file object, if required.
        """
        if exists(f"{gzip_fname}.gz") and not exists(f"{gzip_fname}"):
            fobj.write(f"gzip -v {gzip_fname}\n")

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
        from os import makedirs, getenv
        from os.path import join, dirname, basename, exists, splitext

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
        # Output jifs as tif for easy viewing.
        if ext is not None:
            out_diff_fname = splitext(out_diff_fname)[0] + ext
        elif splitext(out_diff_fname)[-1] == ".jif":
            out_diff_fname = splitext(out_diff_fname)[0] + ".png"
        return out_diff_fname

    def compare_outputs(self, compare_path, output_products):
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

        Returns
        -------
        int
            Binary code: 0 if all comparisons were completed successfully.
        """
        badcomps = []
        goodcomps = []
        missingcomps = []
        missingproducts = []
        compare_strings = []
        LOG.info(
            "**************************************************************************"
            "****"
        )
        LOG.info(
            "**************************************************************************"
            "****"
        )
        LOG.info("*** RUNNING COMPARISONS OF KNOWN OUTPUTS IN %s ***", compare_path)
        LOG.info(
            "**************************************************************************"
            "****"
        )
        LOG.info(
            "**************************************************************************"
            "****"
        )
        LOG.info("")
        from glob import glob
        from os.path import basename, exists, isdir, isfile, join

        compare_basenames = [basename(yy) for yy in glob(compare_path + "/*")]
        final_output_products = []

        for output_product in output_products:
            if isdir(output_product):
                # Skip 'diff' output directory
                continue

            LOG.info(
                "**********************************************************************"
                "****"
            )
            LOG.info("*** COMPARE  %s ***", basename(output_product))
            LOG.info(
                "**********************************************************************"
                "****"
            )

            if basename(output_product) in compare_basenames:
                test_product_func = self.test_products
                goodcomps, badcomps, compare_strings = test_product_func(
                    output_product,
                    join(compare_path, basename(output_product)),
                    goodcomps,
                    badcomps,
                    compare_strings,
                )
            else:
                missingcomps += [output_product]
            final_output_products += [output_product]

            LOG.info("")
        LOG.info(
            "**************************************************************************"
            "****"
        )
        LOG.info(
            "**************************************************************************"
            "****"
        )
        LOG.info(
            "*** DONE RUNNING COMPARISONS OF KNOWN OUTPUTS IN %s ***", compare_path
        )
        LOG.info(
            "**************************************************************************"
            "****"
        )
        LOG.info(
            "**************************************************************************"
            "****"
        )

        product_basenames = [basename(yy) for yy in final_output_products]
        compare_products = []
        comp_found = False
        if len(product_basenames) == 1:
            # this is needed for comparisons of a single product. The code chuck where
            # 'not comp_found' expects a list (len > 1) of product_basenames,
            # whereas the code below assumes only one match is needed
            for compare_product in glob(compare_path + "/*"):
                if isfile(compare_product):
                    compare_products.append(basename(compare_product))
            import numpy as np

            if np.any([comp == product_basenames[0] for comp in compare_products]):
                comp_found = True
        if not comp_found:
            for compare_product in glob(compare_path + "/*"):
                if (
                    isfile(compare_product)
                    and basename(compare_product) not in product_basenames
                ):
                    missingproducts += [compare_product]

        from os import makedirs, getenv

        diffdir = join(compare_path, "diff_test_output_dir_{0}".format(getenv("USER")))
        if not exists(diffdir):
            makedirs(diffdir)

        for goodcompare in goodcomps:
            LOG.warning("GOODCOMPARE %s", goodcompare)

        for missingproduct in missingproducts:
            LOG.warning(
                "MISSINGPRODUCT no %s in output path from current run", missingproduct
            )

        for missingcompare in missingcomps:
            LOG.warning("MISSINGCOMPARE no %s in comparepath", missingcompare)

        for badcompare in badcomps:
            LOG.warning("BADCOMPARE %s", badcompare)

        if len(goodcomps) > 0:
            fname_goodcptest = join(diffdir, "cptest_GOODCOMPARE.txt")
            LOG.info("source {0}".format(fname_goodcptest))
            with open(fname_goodcptest, "w") as fobj:
                fobj.write("mkdir {0}/GOODCOMPARE\n".format(diffdir))
                for goodcomp in goodcomps:
                    if compare_strings is not None:
                        for compare_string in compare_strings:
                            goodcomp = goodcomp.replace(compare_string, "")

                    # For display purposes - tifs are easier to view
                    out_fname = basename(goodcomp).replace(".jif", ".tif")
                    self.print_gunzip_to_file(fobj, goodcomp)
                    fobj.write(
                        "cp {0} {1}/GOODCOMPARE/{2}\n".format(
                            goodcomp, diffdir, out_fname
                        )
                    )
                    self.print_gzip_to_file(fobj, goodcomp)

        if len(missingcomps) > 0:
            fname_cp = join(diffdir, "cp_MISSINGCOMPARE.txt")
            fname_missingcompcptest = join(diffdir, "cptest_MISSINGCOMPARE.txt")
            LOG.interactive(
                "MISSINGCOMPARE Commands to copy %d missing files to test output path.",
                len(missingcomps),
            )
            LOG.interactive("  source {0}".format(fname_missingcompcptest))
            LOG.interactive("  source {0}".format(fname_cp))
            with open(fname_cp, "w") as fobj:
                for missingcomp in missingcomps:
                    self.print_gunzip_to_file(fobj, missingcomp)
                    fobj.write("cp -v {0} {1}/../\n".format(missingcomp, diffdir))
                    self.print_gzip_to_file(fobj, missingcomp)
            with open(fname_missingcompcptest, "w") as fobj:
                fobj.write("mkdir {0}/MISSINGCOMPARE\n".format(diffdir))
                for missingcomp in missingcomps:
                    # For display purposes - tifs are easier to view
                    out_fname = basename(missingcomp).replace(".jif", ".tif")
                    self.print_gunzip_to_file(fobj, missingcomp)
                    fobj.write(
                        "cp -v {0} {1}/MISSINGCOMPARE/{2}\n".format(
                            missingcomp, diffdir, out_fname
                        )
                    )
                    self.print_gzip_to_file(fobj, missingcomp)

        if len(missingproducts) > 0:
            fname_rm = join(diffdir, "rm_MISSINGPRODUCTS.txt")
            fname_missingprodcptest = join(diffdir, "cptest_MISSINGPRODUCTS.txt")
            LOG.interactive(
                "MISSINGPRODUCTS Commands to remove %d "
                "incorrect files from test output path.",
                len(missingproducts),
            )
            LOG.interactive("  source {0}".format(fname_missingprodcptest))
            LOG.interactive("  source {0}".format(fname_rm))
            with open(fname_rm, "w") as fobj:
                for missingproduct in missingproducts:
                    fobj.write("rm -v {0}\n".format(missingproduct))
            with open(fname_missingprodcptest, "w") as fobj:
                fobj.write("mkdir {0}/MISSINGPRODUCTS\n".format(diffdir))
                for missingproduct in missingproducts:
                    # For display purposes - tifs are easier to view
                    out_fname = basename(missingproduct).replace(".jif", ".tif")
                    self.print_gunzip_to_file(fobj, missingproduct)
                    fobj.write(
                        "cp -v {0} {1}/MISSINGPRODUCTS/{2}\n".format(
                            missingproduct, diffdir, out_fname
                        )
                    )
                    self.print_gzip_to_file(fobj, missingproduct)

        if len(badcomps) > 0:
            fname_cp = join(diffdir, "cp_BADCOMPARES.txt")
            fname_badcptest = join(diffdir, "cptest_BADCOMPARES.txt")
            LOG.interactive(
                "BADCOMPARES Commands to copy %d files that had bad comparisons",
                len(badcomps),
            )
            LOG.interactive("  source {0}".format(fname_badcptest))
            LOG.interactive("  source {0}".format(fname_cp))
            with open(fname_cp, "w") as fobj:
                for badcomp in badcomps:
                    if compare_strings is not None:
                        for compare_string in compare_strings:
                            badcomp = badcomp.replace(compare_string, "")
                    self.print_gunzip_to_file(fobj, badcomp)
                    fobj.write("cp -v {0} {1}/../\n".format(badcomp, diffdir))
                    self.print_gzip_to_file(fobj, badcomp)
            with open(fname_badcptest, "w") as fobj:
                fobj.write("mkdir {0}/BADCOMPARES\n".format(diffdir))
                for badcomp in badcomps:
                    badcomp = badcomp.replace("IMAGE ", "")
                    badcomp = badcomp.replace("TEXT ", "")
                    badcomp = badcomp.replace("GEOIPS NETCDF ", "")
                    badcomp = badcomp.replace("GEOTIFF ", "")
                    # For display purposes - tifs are easier to view
                    out_fname = basename(badcomp).replace(".jif", ".tif")
                    self.print_gunzip_to_file(fobj, badcomp)
                    fobj.write(
                        "cp {0} {1}/BADCOMPARES/{2}\n".format(
                            badcomp, diffdir, out_fname
                        )
                    )
                    self.print_gzip_to_file(fobj, badcomp)

        retval = 0
        if len(badcomps) != 0:
            curr_retval = len(badcomps)
            if len(badcomps) > 4:
                curr_retval = 4
            retval += curr_retval << 0
            LOG.info("BADCOMPS %s", len(badcomps))
        if len(missingcomps) != 0:
            curr_retval = len(missingcomps)
            if len(missingcomps) > 4:
                curr_retval = 4
            retval += curr_retval << 0
            LOG.info("MISSINGCOMPS %s", len(missingcomps))
        if len(missingproducts) != 0:
            curr_retval = len(missingproducts)
            if len(missingproducts) > 4:
                curr_retval = 4
            retval += curr_retval << 0
            LOG.info("MISSINGPRODUCTS %s", len(missingproducts))
            retval += len(missingproducts) << 4

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
        self, output_product, compare_product, goodcomps, badcomps, compare_strings
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
            compare_product = self.gunzip_product(compare_product)
        if self.name == "netcdf":
            comp_str = "GEOIPS NETCDF "
        else:
            comp_str = self.name.upper() + " "
        compare_strings += [comp_str]
        if self.module.outputs_match(self, output_product, compare_product):
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
        for output_checker in self.get_plugins():
            checker_found = output_checker.module.correct_type(filename)
            if checker_found:
                checker_name = output_checker.module.name
                break
        if not checker_found:
            raise TypeError("There isn't an output checker built for this data type.")
        return checker_name

    def get_plugin(self, name):
        """Get the output checker plugin corresponding to checker_name and return it."""
        try:
            plug = super().get_plugin(name)
            if self.valid_plugin(plug):
                return plug
        except PluginError:
            plug = super().get_plugin(self.identify_checker(name))
            if self.valid_plugin(plug):
                return plug

    def valid_plugin(self, plugin):
        """Check the validity of the supplied output_checker plugin."""
        if (
            not hasattr(plugin.module, "outputs_match")
            or not hasattr(plugin.module, "correct_type")
            or not hasattr(plugin.module, "call")
        ):
            raise ValidationError(
                "The plugin returned is missing one or more of the following functions."
                "\n[outputs_match, correct_type, call]. Please create those before "
                "using this plugin."
            )
        return True


output_checkers = OutputCheckersInterface()
