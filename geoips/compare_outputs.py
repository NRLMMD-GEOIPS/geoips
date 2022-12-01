# # # Distribution Statement A. Approved for public release. Distribution unlimited.
# # #
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # #
# # # This program is free software:
# # # you can redistribute it and/or modify it under the terms
# # # of the NRLMMD License included with this program.
# # #
# # # If you did not receive the license, see
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/
# # # for more information.
# # #
# # # This program is distributed WITHOUT ANY WARRANTY;
# # # without even the implied warranty of MERCHANTABILITY
# # # or FITNESS FOR A PARTICULAR PURPOSE.
# # # See the included license for more details.

''' Test script for running representative products using data and comparison outputs from geoips_test_data_* '''

import subprocess
import logging
from os.path import basename, join, splitext, dirname, isdir, isfile, exists
LOG = logging.getLogger(__name__)


def is_geotiff(fname):
    ''' Determine if fname is a geotiff file

    Args:
        fname (str) : Name of file to check.

    Returns:
        bool: True if it is an image file, False otherwise.
    '''
    if splitext(fname)[-1] in ['.tif']:
        return True
    return False


def is_image(fname):
    ''' Determine if fname is an image file

    Args:
        fname (str) : Name of file to check.

    Returns:
        bool: True if it is an image file, False otherwise.
    '''
    if splitext(fname)[-1] in ['.png', '.jpg', '.jpeg', '.jif']:
        return True
    return False


def is_geoips_netcdf(fname):
    ''' Check if fname is a geoips formatted netcdf file

    Args:
        fname (str) : Name of file to check.

    Returns:
        bool: True if it is a geoips netcdf file, False otherwise.
    '''
    import xarray
    try:
        xobj = xarray.open_dataset(fname)
    except Exception:
        return False
    from geoips.dev.utils import get_required_geoips_xarray_attrs
    return set(get_required_geoips_xarray_attrs()).issubset(set(xobj.attrs.keys()))


def is_text(fname):
    ''' Check if fname is a text file

    Args:
        fname (str) : Name of file to check.

    Returns:
        bool: True if it is a text file, False otherwise.
    '''

    if splitext(fname)[-1] in ['', '.txt', '.text', '.yaml']:
        with open(fname) as f:
            line = f.readline()
        if isinstance(line, str):
            return True
    return False


def is_gz(fname):
    ''' Check if fname is a gzip file

    Args:
        fname (str) : Name of file to check.

    Returns:
        bool: True if it is an image file, False otherwise.
    '''
    if splitext(fname)[-1] in ['.gz']:
        return True
    return False


def gunzip_product(fname):
    ''' gunzip file fname

    Args:
        fname (str) : File to gunzip

    Returns:
        str: Filename of file after gunzipping
    '''
    LOG.info('**** Gunzipping product for comparisons - will gzip after comparing')
    LOG.info("gunzip %s", fname)
    subprocess.call(['gunzip', fname])
    return splitext(fname)[0]


def gzip_product(fname):
    ''' gzip file fname

    Args:
        fname (str) : File to gzip

    Returns:
        str: Filename of file after gzipping
    '''
    LOG.info('**** Gzipping product - leave things as we found them')
    LOG.info("gzip %s", fname)
    subprocess.call(['gzip', fname])
    return splitext(fname)[0]


def get_out_diff_fname(compare_product, output_product, ext=None):
    from os import makedirs, getenv
    from os.path import exists
    diffdir = join(dirname(compare_product), 'diff_test_output_dir_{0}'.format(getenv('USER')))
    out_diff_fname = join(diffdir, 'diff_test_output_' + basename(output_product))
    if not exists(diffdir):
        makedirs(diffdir)
    # Output jifs as tif for easy viewing.
    if ext is not None:
        out_diff_fname = splitext(out_diff_fname)[0] + ext
    elif splitext(out_diff_fname)[-1] == '.jif':
        out_diff_fname = splitext(out_diff_fname)[0] + '.png'
    return out_diff_fname


def images_match(output_product, compare_product, threshold=0.0000001):
    ''' Use imagemagick compare system command to compare currently produced image to correct image

    Args:
        output_product (str) : Current output product
        compare_product (str) : Path to comparison product
        threshold (float) : DEFAULT 0.0000001, valid range 0-1, maximum allowable RMSE for successful comparison
                                NOTE threshold of 0 will often return False for identicaly tiff files (perhaps due to
                                mismatched headers)

    Returns:
        bool: Return True if images match, False if they differ
    '''
    out_diffimg = get_out_diff_fname(compare_product, output_product)

    call_list = ['compare', '-verbose', '-quiet',
                 '-metric', 'rmse',
                 '-dissimilarity-threshold', '{0:0.15f}'.format(threshold),
                 output_product,
                 compare_product,
                 out_diffimg]

    LOG.info('**Running %s', ' '.join(call_list))
    fullimg_retval = subprocess.call(call_list)
    LOG.info('**Done running compare')

    # call_list = ['compare', '-verbose', '-quiet',
    #              '-metric', 'rmse',
    #              '-dissimilarity-threshold', '{0:0.15f}'.format(threshold),
    #              '-subimage-search',
    #              output_product,
    #              compare_product,
    #              out_diffimg]

    # LOG.info('Running %s', ' '.join(call_list))

    # subimg_retval = subprocess.call(call_list)
    # if subimg_retval != 0 and fullimg_retval != 0:
    #     call_list = ['compare', '-verbose', '-quiet',
    #                  '-metric', 'rmse',
    #                  '-subimage-search',
    #                  output_product,
    #                  compare_product,
    #                  out_diffimg]
    #     subprocess.call(call_list)
    #     LOG.info('    ***************************************')
    #     LOG.info('    *** BAD Images do NOT match exactly ***')
    #     LOG.info('    ***************************************')
    #     return False
    if fullimg_retval != 0:
        LOG.info('    ***************************************')
        LOG.info('    *** BAD Images do NOT match exactly ***')
        LOG.info('    ***************************************')
        return False

    LOG.info('    *************************')
    LOG.info('    *** GOOD Images match ***')
    LOG.info('    *************************')
    # Remove the image if they matched so we don't have extra stuff to sort through.
    from os import unlink as osunlink
    osunlink(out_diffimg)
    return True


def geotiffs_match(output_product, compare_product):
    ''' Use diff system command to compare currently produced image to correct image

    Args:
        output_product (str) : Current output product
        compare_product (str) : Path to comparison product

    Returns:
        bool: Return True if images match, False if they differ
    '''
    out_diffimg = get_out_diff_fname(compare_product, output_product)

    call_list = ['diff',
                 output_product,
                 compare_product]
    LOG.info('Running %s', ' '.join(call_list))
    retval = subprocess.call(call_list)

    subimg_retval = subprocess.call(call_list)
    if retval != 0:
        LOG.info('    *****************************************')
        LOG.info('    *** BAD geotiffs do NOT match exactly ***')
        LOG.info('    *****************************************')
        return False

    LOG.info('    ***************************')
    LOG.info('    *** GOOD geotiffs match ***')
    LOG.info('    ***************************')
    return True


def geoips_netcdf_match(output_product, compare_product):
    ''' Check if two geoips formatted netcdf files match

    Args:
        output_product (str) : Current output product
        compare_product (str) : Path to comparison product

    Returns:
        bool: Return True if products match, False if they differ
    '''
    out_difftxt = get_out_diff_fname(compare_product, output_product)
    diffout = []
    retval = True
    import xarray
    out_xobj = xarray.open_dataset(output_product)
    compare_xobj = xarray.open_dataset(compare_product)

    if out_xobj.attrs != compare_xobj.attrs:
        LOG.info('    **************************************************************')
        LOG.info('    *** BAD GeoIPS NetCDF file attributes do NOT match exactly ***')
        LOG.info('    **************************************************************')
        for attr in out_xobj.attrs.keys():
            if attr not in compare_xobj.attrs:
                diffstr = f'\nattr {attr}\n\noutput\n{out_xobj.attrs[attr]}\n\nnot in comparison\n'
                diffout += [diffstr]
                LOG.info(diffstr)
            elif out_xobj.attrs[attr] != compare_xobj.attrs[attr]:
                diffstr = f'\nattr {attr}\n\noutput\n{out_xobj.attrs[attr]}\n\ncomparison\n{compare_xobj.attrs[attr]}\n'
                diffout += [diffstr]
                LOG.info(diffstr)
        for attr in compare_xobj.attrs.keys():
            if attr not in out_xobj.attrs:
                diffstr = f'\nattr {attr}\n\nnot in output\n\ncomparison\n{compare_xobj.attrs[attr]}\n'
                diffout += [diffstr]
                LOG.info(diffstr)
            elif out_xobj.attrs[attr] != compare_xobj.attrs[attr]:
                diffstr = f'\nattr {attr}\n\noutput\n{out_xobj.attrs[attr]}\n\ncomparison\n{compare_xobj.attrs[attr]}\n'
                diffout += [diffstr]
                LOG.info(diffstr)
        diffout += ['\n']
        retval = False

    if retval is False:
        with open(out_difftxt, 'w') as fobj:
            fobj.writelines(diffout)
        return False

    try:
        xarray.testing.assert_allclose(compare_xobj, out_xobj)
    except AssertionError as resp:
        LOG.info('    ****************************************************************')
        LOG.info('    *** BAD GeoIPS NetCDF files do not match within tolerance *****')
        LOG.info(f'    *** {resp} ***')
        LOG.info('    ****************************************************************')
        diffout += [f'\nxarray objects do not match between current output and comparison\n']
        diffout += [f'\nOut: {out_xobj}\n']
        diffout += [f'\nCompare: {compare_xobj}\n']
        diffout += [f'\n{resp}\n']
        retval = False

    try:
        xarray.testing.assert_identical(compare_xobj, out_xobj)
    except AssertionError as resp:
        LOG.info('    ****************************************************************')
        LOG.info('    *** INFORMATIONAL ONLY assert_identical differences *****')
        LOG.info(f'    *** {resp} ***')
        LOG.info('    ****************************************************************')

    if retval is False:
        with open(out_difftxt, 'w') as fobj:
            fobj.writelines(diffout)
        return False

    return True


def text_match(output_product, compare_product):
    ''' Check if two text files match

    Args:
        output_product (str) : Current output product
        compare_product (str) : Path to comparison product

    Returns:
        bool: Return True if products match, False if they differ
    '''
    retval = subprocess.call(['diff', output_product, compare_product])
    if retval == 0:
        LOG.info('    *****************************')
        LOG.info('    *** GOOD Text files match ***')
        LOG.info('    *****************************')
        return True
    LOG.info('    *******************************************')
    LOG.info('    *** BAD Text files do NOT match exactly ***')
    LOG.info('    *******************************************')
    out_difftxt = get_out_diff_fname(compare_product, output_product)
    with open(out_difftxt, 'w') as fobj:
        subprocess.call(['diff', output_product, compare_product], stdout=fobj)
    return False


def test_product(output_product, compare_product, goodcomps, badcomps, compare_strings):
    ''' Test output_product against "good" product stored in "compare_path".

    Args:
        output_product
    '''
    matched_one = False
    if is_image(output_product):
        matched_one = True
        compare_strings += ['IMAGE ']
        if images_match(output_product, compare_product):
            goodcomps += ['IMAGE {0}'.format(output_product)]
        else:
            badcomps += ['IMAGE {0}'.format(output_product)]

    if is_geotiff(output_product):
        matched_one = True
        compare_strings += ['GEOTIFF ']
        if geotiffs_match(output_product, compare_product):
            goodcomps += ['GEOTIFF {0}'.format(output_product)]
        else:
            badcomps += ['GEOTIFF {0}'.format(output_product)]

    if is_text(output_product):
        matched_one = True
        compare_strings += ['TEXT ']
        if text_match(output_product, compare_product):
            goodcomps += ['TEXT {0}'.format(output_product)]
        else:
            badcomps += ['TEXT {0}'.format(output_product)]

    if is_geoips_netcdf(output_product):
        matched_one = True
        compare_strings += ['GEOIPS NETCDF ']
        if geoips_netcdf_match(output_product, compare_product):
            goodcomps += ['GEOIPS NETCDF {0}'.format(output_product)]
        else:
            badcomps += ['GEOIPS NETCDF {0}'.format(output_product)]

    if not matched_one:
        raise TypeError(f'MISSING TEST for output product: {output_product}')

    return goodcomps, badcomps, compare_strings


def print_gunzip_to_file(fobj, gunzip_fname):
    if exists(f'{gunzip_fname}.gz') and not exists(f'{gunzip_fname}'):
        fobj.write(f'gunzip -v {gunzip_fname}.gz\n')


def print_gzip_to_file(fobj, gzip_fname):
    if exists(f'{gzip_fname}.gz') and not exists(f'{gzip_fname}'):
        fobj.write(f'gzip -v {gzip_fname}\n')


def compare_outputs(compare_path, output_products, test_product_func=None):
    ''' Compare the "correct" imagery found in comparepath with the list of current output_products

    Args:
        comparepath (str) : Path to directory of "correct" products - filenames must match output_products
        output_products (list) : List of strings of current output products, to compare with products in compare_path
        test_product_func (function) : DEFAULT: None (which uses geoips.compare_outputs.test_product)
                                      *Alternative function to be used for testing output product
                                        * Call signature must be:
                                            * output_product, compare_product, goodcomps, badcomps, compare_strings
                                        * Return must be:
                                            * goodcomps, badcomps, compare_strings



    Returns:
        int: Binary code: Good products, bad products, missing products
    '''
    try:
        from shutil import which
        if not which('compare'):
            raise OSError('Imagemagick compare does not exist, install if you want to check outputs')
    except ImportError:
        pass
    badcomps = []
    goodcomps = []
    missingcomps = []
    missingproducts = []
    compare_strings = []
    LOG.info('********************************************************************************************')
    LOG.info('********************************************************************************************')
    LOG.info('*** RUNNING COMPARISONS OF KNOWN OUTPUTS IN %s ***', compare_path)
    LOG.info('********************************************************************************************')
    LOG.info('********************************************************************************************')
    LOG.info('')
    from glob import glob

    compare_basenames = [basename(yy) for yy in glob(compare_path + '/*')]
    final_output_products = []

    for output_product in output_products:
        if isdir(output_product):
            # Skip 'diff' output directory
            continue

        LOG.info('********************************************************************************************')
        LOG.info('*** COMPARE  %s ***', basename(output_product))
        LOG.info('********************************************************************************************')

        rezip = False
        if is_gz(output_product):
            rezip = True
            output_product = gunzip_product(output_product)

        if basename(output_product) in compare_basenames:
            if test_product_func is None:
                test_product_func = test_product
            goodcomps, badcomps, compare_strings = test_product_func(output_product,
                                                                     join(compare_path, basename(output_product)),
                                                                     goodcomps,
                                                                     badcomps,
                                                                     compare_strings)
        else:
            missingcomps += [output_product]
        final_output_products += [output_product]

        # Make sure we leave things as we found them
        if rezip is True:
            gzip_product(output_product)

        LOG.info('')
    LOG.info('********************************************************************************************')
    LOG.info('********************************************************************************************')
    LOG.info('*** DONE RUNNING COMPARISONS OF KNOWN OUTPUTS IN %s ***', compare_path)
    LOG.info('********************************************************************************************')
    LOG.info('********************************************************************************************')

    product_basenames = [basename(yy) for yy in final_output_products]
    for compare_product in glob(compare_path + '/*'):
        if isfile(compare_product) and basename(compare_product) not in product_basenames:
            missingproducts += [compare_product]

    from os import makedirs, getenv
    from os.path import exists
    diffdir = join(compare_path, 'diff_test_output_dir_{0}'.format(getenv('USER')))
    if not exists(diffdir):
        makedirs(diffdir)

    for goodcompare in goodcomps:
        LOG.warning('GOODCOMPARE %s', goodcompare)

    for missingproduct in missingproducts:
        LOG.warning('MISSINGPRODUCT no %s in output path from current run', missingproduct)

    for missingcompare in missingcomps:
        LOG.warning('MISSINGCOMPARE no %s in comparepath', missingcompare)

    for badcompare in badcomps:
        LOG.warning('BADCOMPARE %s', badcompare)

    if len(goodcomps) > 0:
        fname_goodcptest = join(diffdir, 'cptest_GOODCOMPARE.txt')
        print('source {0}'.format(fname_goodcptest))
        with open(fname_goodcptest, 'w') as fobj:
            fobj.write('mkdir {0}/GOODCOMPARE\n'.format(diffdir))
            for goodcomp in goodcomps:

                if compare_strings is not None:
                    for compare_string in compare_strings:
                        goodcomp = goodcomp.replace(compare_string, '')

                # For display purposes - tifs are easier to view
                out_fname = basename(goodcomp).replace('.jif', '.tif')
                print_gunzip_to_file(fobj, goodcomp)
                fobj.write('cp {0} {1}/GOODCOMPARE/{2}\n'.format(goodcomp, diffdir, out_fname))
                print_gzip_to_file(fobj, goodcomp)

    if len(missingcomps) > 0:
        fname_cp = join(diffdir, 'cp_MISSINGCOMPARE.txt')
        fname_missingcompcptest = join(diffdir, 'cptest_MISSINGCOMPARE.txt')
        print('source {0}'.format(fname_missingcompcptest))
        print('# source {0}'.format(fname_cp))
        with open(fname_cp, 'w') as fobj:
            for missingcomp in missingcomps:
                print_gunzip_to_file(fobj, missingcomp)
                fobj.write('cp -v {0} {1}/../\n'.format(missingcomp, diffdir))
                print_gzip_to_file(fobj, missingcomp)
        with open(fname_missingcompcptest, 'w') as fobj:
            fobj.write('mkdir {0}/MISSINGCOMPARE\n'.format(diffdir))
            for missingcomp in missingcomps:
                # For display purposes - tifs are easier to view
                out_fname = basename(missingcomp).replace('.jif', '.tif')
                print_gunzip_to_file(fobj, missingcomp)
                fobj.write('cp -v {0} {1}/MISSINGCOMPARE/{2}\n'.format(missingcomp, diffdir, out_fname))
                print_gzip_to_file(fobj, missingcomp)

    if len(missingproducts) > 0:
        fname_rm = join(diffdir, 'rm_MISSINGPRODUCTS.txt')
        fname_missingprodcptest = join(diffdir, 'cptest_MISSINGPRODUCTS.txt')
        print('source {0}'.format(fname_missingprodcptest))
        print('# source {0}'.format(fname_rm))
        with open(fname_rm, 'w') as fobj:
            for missingproduct in missingproducts:
                fobj.write('rm -v {0}\n'.format(missingproduct))
        with open(fname_missingprodcptest, 'w') as fobj:
            fobj.write('mkdir {0}/MISSINGPRODUCTS\n'.format(diffdir))
            for missingproduct in missingproducts:
                # For display purposes - tifs are easier to view
                out_fname = basename(missingproduct).replace('.jif', '.tif')
                print_gunzip_to_file(fobj, missingproduct)
                fobj.write('cp -v {0} {1}/MISSINGPRODUCTS/{2}\n'.format(missingproduct, diffdir, out_fname))
                print_gzip_to_file(fobj, missingproduct)

    if len(badcomps) > 0:
        fname_cp = join(diffdir, 'cp_BADCOMPARES.txt')
        fname_badcptest = join(diffdir, 'cptest_BADCOMPARES.txt')
        print('source {0}'.format(fname_badcptest))
        print('# source {0}'.format(fname_cp))
        with open(fname_cp, 'w') as fobj:
            for badcomp in badcomps:

                if compare_strings is not None:
                    for compare_string in compare_strings:
                        badcomp = badcomp.replace(compare_string, '')
                print_gunzip_to_file(fobj, badcomp)
                fobj.write('cp -v {0} {1}/../\n'.format(badcomp, diffdir))
                print_gzip_to_file(fobj, badcomp)
        with open(fname_badcptest, 'w') as fobj:
            fobj.write('mkdir {0}/BADCOMPARES\n'.format(diffdir))
            for badcomp in badcomps:
                badcomp = badcomp.replace('IMAGE ', '')
                badcomp = badcomp.replace('TEXT ', '')
                badcomp = badcomp.replace('GEOIPS NETCDF ', '')
                badcomp = badcomp.replace('GEOTIFF ', '')
                # For display purposes - tifs are easier to view
                out_fname = basename(badcomp).replace('.jif', '.tif')
                print_gunzip_to_file(fobj, badcomp)
                fobj.write('cp {0} {1}/BADCOMPARES/{2}\n'.format(badcomp, diffdir, out_fname))
                print_gzip_to_file(fobj, badcomp)

    retval = 0
    if len(badcomps) != 0:
        curr_retval = len(badcomps)
        if len(badcomps) > 4:
            curr_retval = 4
        retval += curr_retval << 0
        LOG.info('BADCOMPS %s', len(badcomps))
    if len(missingcomps) != 0:
        curr_retval = len(missingcomps)
        if len(missingcomps) > 4:
            curr_retval = 4
        retval += curr_retval << 0
        LOG.info('MISSINGCOMPS %s', len(missingcomps))
    if len(missingproducts) != 0:
        curr_retval = len(missingproducts)
        if len(missingproducts) > 4:
            curr_retval = 4
        retval += curr_retval << 0
        LOG.info('MISSINGPRODUCTS %s', len(missingproducts))
        retval += len(missingproducts) << 4

    LOG.info('retval: %s', bin(retval))
    if retval != 0:
        LOG.info('Nonzero return value indicates error, 6 bit binary code: WXY where:')
        LOG.info('    Y (0-1): BADCOMP: number of bad comparisons found between comparepath and current run output path')
        LOG.info('    X (2-3): MISSINGCOMP: Number of products missing in compare path but existing in current output path')
        LOG.info('    W (4-5): MISSINGPROD: Number of products existing in comparepath, but missing in current output path')

    return retval
