# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Test script for representative product comparisons."""

import subprocess
import logging
from os.path import splitext
from shutil import copy
from os.path import exists, join
from importlib.resources import files
import os

from geoips.base_class_plugins.output_checkers import BaseOutputCheckerPlugin
from geoips.commandline.log_setup import log_with_emphasis
from geoips.geoips_utils import get_numpy_seeded_random_generator

predictable_random = get_numpy_seeded_random_generator()

LOG = logging.getLogger(__name__)


class TextOutputCheckerPlugin(BaseOutputCheckerPlugin):
    """Text Output Checker Plugin Class.

    Inherits from BaseOutputCheckerPlugin, which contains shared functionality among
    output_checker plugins. Responsible for comparing two text files
    (produced, expected) within a given threshold.
    """

    interface = "output_checkers"
    family = "standard"
    name = "text"

    def write_percent_of_list_elements_to_file_and_return_filepath(
        self,
        list_with_lines,
        filename,
        percent_to_write,
        random_func=predictable_random.random,
    ):
        """Grabs a random subset of lines in a file and writes them."""
        threshold = float(100 - percent_to_write) / 100
        with open(filename, "w") as f:
            for line in list_with_lines:
                if random_func() > threshold:
                    f.write(line)

    def get_test_files(self, test_data_dir):
        """Return a series of varied text files."""
        save_dir = join(test_data_dir, "scratch", "unit_tests", "test_text")
        if not exists(save_dir):
            os.mkdir(save_dir, exists_ok=True)

        text_path = str(files("geoips") / "plugins/txt/ascii_palettes/tpw_cimss.txt")

        comp_path = join(save_dir, "compare.txt")
        copy(text_path, comp_path)
        with open(comp_path, mode="r") as comp_txt:
            comp_text_contents = comp_txt.readlines()

        return comp_path, [
            self.write_percent_of_list_elements_to_file_and_return_filepath(
                comp_text_contents, join(save_dir, "matched.txt"), 100
            ),
            self.write_percent_of_list_elements_to_file_and_return_filepath(
                comp_text_contents, join(save_dir, "slightly_mismatch.txt"), 95
            ),
            self.write_percent_of_list_elements_to_file_and_return_filepath(
                comp_text_contents, join(save_dir, "bad_mismatch.txt"), 75
            ),
        ]

    def perform_test_comparisons(self, compare_file, test_files):
        """Test the comparison of two text files with the Text Output Checker.

        Parameters
        ----------
        compare_file : str
            Path to the comparison (baseline) file.
        test_files : list[str]
            List of test file paths [matched, close_mismatch, bad_mismatch].

        Raises
        ------
        AssertionError
            If any comparison result doesn't match expected outcome.
        """
        for path_idx in range(len(test_files)):
            retval = self.outputs_match(
                test_files[path_idx],
                compare_file,
            )
            if path_idx == 0:
                assert retval is True
            else:
                assert retval is False

    def correct_file_format(self, fname):
        """Check if fname is a text file.

        Parameters
        ----------
        fname : str
            Name of file to check.

        Returns
        -------
        bool
            True if it is a text file, False otherwise.
        """
        if splitext(fname)[-1] in ["", ".txt", ".text", ".yaml"]:
            with open(fname) as f:
                line = f.readline()
            if isinstance(line, str):
                return True
        return False

    def outputs_match(self, output_product, compare_product):
        """Check if two text files match.

        Parameters
        ----------
        output_product : str
            Full path to current output product
        compare_product : str
            Full path to "good" comparison product

        Returns
        -------
        bool
            Return True if products match, False if they differ
        """
        ret = subprocess.run(
            ["diff", output_product, compare_product],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        LOG.debug(ret.stdout)
        if ret.returncode == 0:
            log_with_emphasis(LOG.info, "GOOD Text files match")
            return True

        out_difftxt = self.get_out_diff_fname(compare_product, output_product)
        with open(out_difftxt, "w") as fobj:
            subprocess.call(["diff", output_product, compare_product], stdout=fobj)
        log_with_emphasis(
            LOG.interactive,
            "BAD Text files do NOT match exactly",
            f"output_product: {output_product}",
            f"compare_product: {compare_product}",
            f"out_difftxt: {out_difftxt}",
        )
        return False

    def call(self, compare_path, output_products):
        """Compare the "correct" text found the list of current output_products.

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
        retval = self.compare_outputs(
            compare_path,
            output_products,
        )
        return retval


PLUGIN_CLASS = TextOutputCheckerPlugin
