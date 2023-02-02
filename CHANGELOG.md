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

## NRLMMD-GEOIPS/geoips#83: 2023-01-31, fix bug in actions on forks
### Actions
* Update docker actions to only push to ghcr.io from `main` or for new tags.
* Disable cache-to and set cache-from to use `latest` tag.
## NRLMMD-GEOIPS/geoips#59: 2023-02-01, fix date and ls on mac
### Fix linux commands `date` and `ls` on Mac
* Updated `setup.sh` and `tests/download_noaa_aws.sh` to use `gdate` on Mac
* Updated `geoips/interface_modules/output_formats/text_winds.py` to use `os.stat` rather
  than `ls --full-time` to get file creation time.
## NRLMMD-GEOIPS/geoips#86: 2023-01-31, disallow PR that don't change CHANGELOG.md
### Actions
* Add test to block merging until CHANGELOG.md has been updated
```
.github/workflows/validate-pull-request.yaml
```
## NRLMMD-GEOIPS/geoips#68: 2023-01-25, change full install requirements
### Installation and Test
* Copied extra requirements to "install_requires" in "setup.py"

# v1.6.1: 2023-01-04, update formatting, test full install, bug fixes

## GEOIPS#144: 2023-01-04, slight doc updates.
### Documentation Updates
* Replace full links with relative - will work on different branches
* Slightly rearrange installation.rst - only include a single "Complete conda-based
  installation" section to avoid confusion.

## GEOIPS#153: 2023-01-04, GEOIPS->GEOIPS_PACKAGES_DIR/geoips
### Testing Updates
* Replace all instances of $GEOIPS with $GEOIPS_PACKAGES_DIR/geoips
  * $GEOIPS is an optional environment variable.

## GEOIPS#149: 2023-01-04, GEOIPS_BASEDIR/test_data->GEOIPS_TESTDATA_DIR
### Testing Updates
* Replacing all instances of GEOIPS_BASEDIR/test_data with GEOIPS_TESTDATA_DIR
* REMOVE tests/README.md - deprecated, info now included in template repos.

## GEOIPS#147: 2023-01-03, add test_full_install.sh
### Testing Updates
* Add script to obtain and test all test repos.
* Add "setup_test_repos" to setup.sh, which clones, updates, and uncompresses test repo.
```
setup.sh
tests/test_full_install.sh
```

## GEOIPS#145: 2023-01-03, remove numpy aliases to builtin types
### Bug fixes
* Update AHI HSD reader to replace numpy.bool with bool
* numpy v1.20.0 no longer allows using numpy aliases to builtin types.
```
geoips/interface_modules/readers/ahi_hsd.py
```

## GEOIPS#126: 2022-12-29, update code style
### Major New Functionality
* new file: tests/utils/check_code.sh
    * black
    * flake8
    * bandit
### Documentation and Formatting Updates
* Update all docstrings to numpy formatting
* Apply black with default options to all Python code
* Begin applying flake8 updates

## GEOIPS#2: 2022-12-06, update interface types
### Major New Functionality
#### geoips/interface_modules/filename_formats/basic_fname.py
* Add very basic filename module - just put a straightforwardly named file in a specified directory
    * Only relying on required geoips xarray attributes, passed product name, and area_def.area_id if defined
#### geoips/interface_modules/procflows/single_source.py
* Denote output families that require a specified list of output files in advance separately from
  those that do NOT require a complete list of files in advance
    * Allows dynamically determining output filenames from within an output format.
    * Do not automatically generate metadata if output filenames not pre-specified
* Add support for unsectored products that require area_def
#### geoips/dev/filename.py
* Add xarray_area_product_to_filename filename type
    * Only xarray, area_def, and product_name as args, and output_type and basedir as kwargs
    * Other filename types have a LOT of required kwargs
#### geoips/dev/output.py
* Add xrdict_area_product_to_outlist output type
    * xarray_dict, area_def, product_name args
    * NOTE: output_fnames is NOT included in argument list, which means resulting file list will
      NOT be checked for consistency.
#### geoips/dev/product.py
* Add unsectored_xarray_dict_area_to_output_format
    * This indicates procflow must process this unsectored data type from within the area_def loop.
    * Ie, unsectored read, but final product may require area information
#### geoips/interface_modules/output_formats/imagery_clean.py
* Allow using "order" attribute on xarray object to set zorder in plot
#### tests/download_noaa_aws.sh
* Allow wildcards in NOAA AWS downloads


# v1.6.0: 2022-11-28, open source release

## GEOIPS#11: 2022-12-12, use original AMSR2-MBT filenames
### Test Repo Updates
* Renamed AMSR2 test datasets to use original filenames, for reference.
* Update test scripts/outputs accordingly
    * Source filename in call and YAML metadata output
```
modified: tests/scripts/amsr2.config_based_overlay_output_low_memory.sh
modified: tests/scripts/amsr2.config_based_overlay_output.sh
modified: tests/scripts/amsr2.tc.89H-Physical.imagery_annotated.sh
modified: tests/outputs/amsr2.tc_overlay.37pct.imagery_annotated_over_Infrared-Gray/20200518_073601_IO012020_amsr2_gcom-w1_37pct_140kts_95p89_res1p0-cr100-bgInfrared-Gray.png.yaml
modified: tests/outputs/amsr2.tc_overlay.89pct.imagery_annotated_over_Infrared-Gray/20200518_073601_IO012020_amsr2_gcom-w1_89pct_140kts_98p32_res1p0-cr100-bgInfrared-Gray.png.yaml
modified: tests/outputs/amsr2.tc_overlay.37pct.imagery_annotated_over_Visible/20200518_073601_IO012020_amsr2_gcom-w1_37pct_140kts_95p89_res1p0-cr100-bgVisible.png.yaml
modified: tests/outputs/amsr2.tc_overlay.89pct.imagery_annotated_over_Visible/20200518_073601_IO012020_amsr2_gcom-w1_89pct_140kts_98p32_res1p0-cr100-bgVisible.png.yaml
modified: tests/outputs/amsr2.tc.89H-Physical.imagery_annotated/20200518_073601_IO012020_amsr2_gcom-w1_89H-Physical_140kts_100p00_res1p0-cr300.png.yaml
```

## GEOIPS#119: 2022-11-16, installation updates, test script bug fixes
### Bug fixes
#### geoips/filenames/duplicate_files.py
* Fix indentation for if/else duplicate removal SKIP
#### setup/bash_setup/check_continue
* Add +z to variable checks
* Failed with different invocations of calling the script
#### Update YAML metadata storm_start_datetime
```tests/outputs/amsr2_ocean.tc.windspeed.imagery_clean/20200518_073601_IO012020_amsr2_gcom-w1_windspeed_140kts_85p45_1p0-clean.png.yaml
### Documentation Updates
#### Add Contributors documentation page
* Link to contributors page from README
* Link to git-workflow.rst from Contributors page
* Replace full URLs with linked text in git-workflow.rst
```
new file: docs/contributors.rst
modified: README.md
modified: docs/git-workflow.rst
modified: docs/setup-new-plugin.rst
```
#### Simplify README and installation
* Only include next step once in check_continue output, for simplicity
* Remove direct installation steps from README.md
* Include more generalized information in README, with link to full documentation/installation.
* Move the complete conda-based installation to the bottom of docs/installation.rst
* Include system requirements, and a basic geoips installation process (not requiring full conda based install)
  in installation.rst
```
modified: README.md
modified: docs/installation.rst
modified: setup/bash_setup/check_continue
```
### Testing Updates
* Add additional AMSR2 test scripts to test_all.sh - not previously tested.
* Update YAML metadata output for previously non-tested AMSR2 scripts to include storm_start_datetime
```
modified: tests/outputs/amsr2.tc_overlay.37pct.imagery_annotated_over_Infrared-Gray/20200518_073601_IO012020_amsr2_gcom-w1_37pct_140kts_95p89_res1p0-cr100-bgInfrared-Gray.png.yaml
modified: tests/outputs/amsr2.tc_overlay.37pct.imagery_annotated_over_Visible/20200518_073601_IO012020_amsr2_gcom-w1_37pct_140kts_95p89_res1p0-cr100-bgVisible.png.yaml
modified: tests/outputs/amsr2.tc_overlay.89pct.imagery_annotated_over_Infrared-Gray/20200518_073601_IO012020_amsr2_gcom-w1_89pct_140kts_98p32_res1p0-cr100-bgInfrared-Gray.png.yaml
modified: tests/outputs/amsr2.tc_overlay.89pct.imagery_annotated_over_Visible/20200518_073601_IO012020_amsr2_gcom-w1_89pct_140kts_98p32_res1p0-cr100-bgVisible.png.yaml
modified: tests/outputs/amsr2_ocean.tc.windspeed.imagery_clean/20200518_073601_IO012020_amsr2_gcom-w1_windspeed_140kts_85p45_1p0-clean.png.yaml
modified: tests/test_all.sh
```
### Installation Updates
* Only re-set GEOIPS_REPO_URL if it is not already set.  Assume if someone explicitly sets it, they mean it.
```
modified:   setup/config_geoips
```
* Add --config option for rclone lsf command, was failing without ~/.config/rclone/rclone.conf
```
modified: tests/download_noaa_aws.sh
```


# v1.5.3: 2022-11-07, update python install process, alternate command line args funcs, unique storm dirnames for invests, bug fixes
## GEOIPS#108: 2022-11-04, bug fixes
### Documentation Updates
* Clarify steps in updating CHANGELOG during internal release process
```
modified: CHANGELOG_TEMPLATE.md
```
### Test Repo Update
* Update abi.tc.Infrared.imagery_annotated metadata YAML
    * Add Add storm_start_datetime to metadata yaml
```
modified:   tests/outputs/abi.tc.Infrared.imagery_annotated/20200918_195020_AL202020_abi_goes-16_Infrared_110kts_100p00_1p0.png.yaml
```

## GEOIPS#114: 2022-10-27, fix sun.set_time bug in overpass_predictor.py
### Bug fixes
#### Fix sun.set_time bug in overpass_predictor.py
* Previously only check sun.rise_time
* sun.rise_time can be valid while sun.set_time is None, so must check both.
* return None if either sun.rise_time or sun.set_time is None
```
modified:   geoips/sector_utils/overpass_predictor.py
```

## GEOIPS#113: 2022-10-27, VIIRS lat/lon variables may contain unmasked fill values
### Bug fix
#### modified: geoips/interface_modules/readers/viirs_netcdf.py
* Loop through xarray_return data types, and mask latitude/longitude by their fill value

## GEOIPS#111: 2022-10-27, cowvr edge case - no usable sectored data
### Bug fix
#### modified: geoips/interface_modules/procflows/config_based.py
* Add check if sectored data contains any usable data
    * Only add variable to all_vars list if sectored data set is not entirely comprised of NaNs
#### modified: geoips/interface_modules/procflows/single_source.py
* Add check if sectored data contains any usable data
    * Only add variable to all_vars list if sectored data set is not entirely comprised of NaNs

## GEOIPS#61: 2022-10-27, add sectored and unsectored AMSR2 winds outputs
### Major New Functionality
#### Add sectored and unsectored products to product_inputs/amsr2.yaml
* Allows producing sectored and unsectored text winds outputs
```
modified: geoips/yaml_configs/product_inputs/amsr2.yaml
```

## GEOIPS#8: 2022-10-21, get_product allow empty dict, bug fixes
#### modified: geoips/dev/product.py
* Previously would only replace individual fields within dictionaries in product_inputs
* Now, if an empty dictionary is included within product_inputs, it will replace the entire product_params
  dictionary with an empty dictionary.
* This is useful when using product_templates, and replacing the algorithm or colormap, etc
### Test Repo Updates
#### Update ASCAT UHR test data path
* Renamed ASCAT UHR test data subdirectories with additional test cases.
```
modified: tests/scripts/ascat_uhr.tc.wind-ambiguities.imagery_windbarbs.sh
```
#### Turn off minor ticks
* matplotlib 3.6.0 sometimes has inconsistent results with including minor ticks or not.
* Unclear why it impacts some colorbars and not others.
* We may eventually add support for including minor ticks within mpl_colors_info, but for now
* explicitly turn off minor ticks so outputs will continue to match (use the old default).
```
modified: geoips/image_utils/mpl_utils.py
```

## GEOIPS#103: 2022-10-17, create unique storm dirnames for invests
### Major New Functionality
#### geoips/interface_modules/filename_formats/tc_clean_fname.py
* Allow passing "output_dict" to allow using unique directory name for INVESTS
#### geoips/interface_modules/filename_formats/tc_fname.py
* def tc_fname
    * Allow passing output_dict to provide current output parameters for overall filename specifications
* def assemble_tc_fname
    * Allow passing both "output_dict" and "sector_info" to allow timestamp in dirname for INVESTS
#### geoips/interface_modules/filename_formats/utils/tc_file_naming.py
* Allow passing both "output_dict" and "sector_info" to support .%Y%m%d%H dirname for INVESTS
    * output_dict['file_path_modifications']['unique_invest_dirs'] True
    * storm_start_datetime is datetime object
        * sector_info['original_storm_start_datetime'] if it exists, else
        * sector_info['storm_start_datetime']
    * storm number > 69 (ie, invest)
    * output_dict['file_path_modifications']['existing_invest_dirs_allowable_time_diff'] > 0
        * If specified, use existing directory closest in time to storm_start_datetime
        * If none exist, use storm_start_datetime appended to INVEST directory
        * Ie, SH932020.2020020506 vs SH932020
        * If SH932020.2020020406 exists, would use that rather than creating 2020020506
        * SH162020 does NOT contain the extra storm start datetime information
#### geoips/interface_modules/trackfile_parsers/bdeck_parser.py
* Add storm_start_datetime field to bdeck sector info
    * pull from first entry in bdeck file
* Add original_storm_start_datetime field to bdeck sector_info
    * Pull from filename if available (since bdeck entries can change)
    * DO NOT INCLUDE in dictionary if it is not available
    * If it exists, this will be a more consistent value than storm_start_datetime (which can change with
      subsequent deck files)
#### geoips/interface_modules/filename_formats/metadata_default_fname.py
* def metadata_default_fname
    * Allow passing output_dict to provide current output parameters for overall filename specifications
* def assemble_metadata_default_fname
    * Allow passing both "output_dict" and "sector_info" to allow timestamp in dirname for INVESTS
#### geoips/interface_modules/filename_formats/text_winds_tc_fname.py
* def text_winds_tc_fname
    * Allow passing output_dict to provide current output parameters for overall filename specifications
* def assemble_text_winds_tc_fname
    * Allow passing both "output_dict" and "sector_info" to allow timestamp in dirname for INVESTS
### Test Repo Updates
#### Add storm_start_datetime to YAML metadata outputs
    * modified: tests/outputs/abi.tc.IR-BD.imagery_annotated/20200918_195020_AL202020_abi_goes-16_IR-BD_110kts_100p00_1p0.png.yaml
    * modified: tests/outputs/abi.tc.Visible.imagery_annotated/20200918_195020_AL202020_abi_goes-16_Visible_110kts_100p00_1p0.png.yaml
    * modified: tests/outputs/amsr2.tc.89H-Physical.imagery_annotated/20200518_073601_IO012020_amsr2_gcom-w1_89H-Physical_140kts_100p00_res1p0-cr300.png.yaml
    * modified: tests/outputs/amsub_mirs.tc.183-3H.imagery_annotated/20210419_235400_WP022021_amsu-b_metop-a_183-3H_115kts_100p00_1p0.png.yaml
    * modified: tests/outputs/ascat_knmi.tc.windbarbs.imagery_windbarbs_clean/20210421_014248_WP022021_ascat_metop-c_windbarbs_120kts_78p20_0p5-clean.png.yaml
    * modified: tests/outputs/ascat_low_knmi.tc.windbarbs.imagery_windbarbs/20210421_014156_WP022021_ascat_metop-c_windbarbs_120kts_35p17_1p0.png.yaml
    * modified: tests/outputs/ascat_uhr.tc.wind-ambiguities.imagery_windbarbs/20210421_014200_WP022021_ascatuhr_metop-c_wind-ambiguities_120kts_100p00_0p1.png.yaml
    * modified: tests/outputs/gmi.tc.89pct.imagery_clean/20200917_172045_AL202020_gmi_GPM_89pct_115kts_78p16_res1p0-cr300-clean.png.yaml
    * modified: tests/outputs/hy2.tc.windspeed.imagery_annotated/20211202_084039_WP272021_hscat_hy-2b_windspeed_95kts_97p06_1p0.png.yaml
    * modified: tests/outputs/mimic_fine.tc.TPW-PWAT.imagery_annotated/20210419_230000_WP022021_mimic_tpw_TPW-PWAT_115kts_100p00_1p0.png.yaml
    * modified: tests/outputs/oscat_knmi.tc.windbarbs.imagery_windbarbs/20210209_025351_SH192021_oscat_scatsat-1_windbarbs_135kts_75p10_1p0.png.yaml
    * modified: tests/outputs/saphir.tc.183-3HNearest.imagery_annotated/20210209_003103_SH192021_saphir_meghatropiques_183-3HNearest_135kts_88p76_1p0.png.yaml
    * modified: tests/outputs/sar.tc.nrcs.imagery_annotated/20181025_203206_WP312018_sar-spd_sentinel-1_nrcs_130kts_58p51_res1p0-cr300.png.yaml
    * modified: tests/outputs/ssmi.tc.37pct.imagery_clean/20200519_080900_IO012020_ssmi_F15_37pct_110kts_50p65_1p0-clean.png.yaml
    * modified: tests/outputs/viirsday.tc.Night-Vis-IR.imagery_annotated/20210209_074210_SH192021_viirs_noaa-20_Night-Vis-IR_130kts_100p00_1p0.png.yaml
### Bug fixes
#### Do not attempt to set_ticks if cbar_ticks is not defined
    geoips/image_utils/mpl_utils.py
#### Replace fig.savefig frameon=False argument with facecolor="none"
* frameon deprecated maplotlib v3.1.0, support removed v3.6.0
* facecolor="none" also works with 3.5.x
* https://matplotlib.org/stable/api/prev_api_changes/api_changes_3.1.0.html?highlight=frameon
* Updated files:
```
geoips/image_utils/mpl_utils.py
geoips/interface_modules/output_formats/unprojected_image.py
```

## GEOIPS#8: 2022-09-29, allow alternate command line args funcs
### Enhancements
#### new: tests/sectors/tc_bdecks/bwp142022.dat
#### modified: geoips/commandline/args.py
* Allow passing alternate check_args_func and get_args_func to get_command_line_args
* Default output_format None vs imagery_annotated
#### modified: geoips/commandline/run_procflow.py
* Allow passing alternate "get_command_line_args" func to run_procflow main
#### modified: geoips/dev/product.py
* Add 'xarray_dict_to_output_format' product type
* Allow specifying "product_template" within product_params YAML as well as product_inputs
#### modified: geoips/image_utils/mpl_utils.py
* Support additional mpl_colors_info fields
    * explicit colorbar positioning, maintain previous defaults if not set
        * cbar_ax_left_start_pos
            * If set, explicitly set the left start position for the colorbar axis, relative to figure
            * Else if 'cbar_full_width' is set, set to "left_margin"
            * Else default to 2*left_margin
        * cbar_ax_bottom_start_pos
            * If set, explicitly set the bottom start position for the colorbar axis, relative to figure
            * Else default to 0.05
        * cbar_ax_width
            * If set, explicitly set the width (left to right) of the colorbar axis, relative to figure
            * Else if 'cbar_full_width' is set, set to right_margin - left_margin
            * Else default to 1 - 4*left_margin
        * cbar_ax_height
            * If set, explicitly set the height (bottom to top) of the colorbar axis, relative to figure
            * Else, default to 0.02
    * explicit colorbar keyword args (mpl_colors_info['colorbar_kwargs'])
        * colorbar_kwargs['orientation']
            * If set, explicitly set orientation
            * Else, default to 'horizontal'
        * colorbar_kwargs['extend']
            * If set, explicitly set extend option to colorbar call
            * Else, default to 'both'
        * colorbar_kwargs['spacing']
            * If set, explicitly set 'spacing' option to colorbar call
            * Else, if 'cbar_spacing' set, use mpl_colors_info['cbar_spacing']
            * Else, default to 'proportional'
    * explicit set_ticks_kwargs args (mpl_colors_info['set_ticks_kwargs'])
        * set_ticks_kwargs['size']
            * If set, explicitly set 'size' option to set_ticks call
            * Else, default to 'small'
        * set_ticks_kwargs['labels']
            * If set, explicitly set 'labels' option to set_ticks call
            * Else, default to mpl_colors_info['cbar_tick_labels']
            * Else, default to mpl_colors_info['cbar_ticks']
    * explicit set_label_kwargs (mpl_colors_info['set_label_kwargs])
        * set_label_kwargs['size']
            * If set, explicitly set 'size' option to set_label call
            * Else, default to rc_params['font.size']
* Call pyplot.colorbar vs fig.colorbar
    * Pass "cbar_kwargs" in directly to allow specifying arbitrary colorbar options via mpl_colors_info
* Pass **set_ticks_kwargs to cbar.set_ticks call
* Pass **set_label_kwargs to cbar.set_label call
#### modified: geoips/interface_modules/output_formats/imagery_clean.py
* Support plotting on existing figure and axis
    * Only create fig, main_ax, and mapobj if not passed in explicitly
    * If fig, main_ax, and mapobj passed, plot on existing
    * Only output final image if output_fnames is not None
#### modified: geoips/interface_modules/output_formats/imagery_windbarbs.py
* Support plotting on existing figure and axis
    * Update output_clean_windbarbs function to take fig, main_ax, and mapobj arguments
    * Only create figure, main axis, and mapobj if not passed
    * Only output image file if clean_fnames is not None
* Allow specifying barb_sizes in product_definition
    * If 'barb_sizes' is in xarray_obj.attrs['product_definition'], use those values
        * thinning
        * barb_length
        * line_width
        * sizes_dict
        * rain_size
    * Else, default to former operation based on product_name == 'windbarbs' or 'wind-ambiguities'
#### modified: geoips/interface_modules/output_formats/imagery_windbarbs_clean.py
* Support plotting on existing figure and axis
    * Update imagery_windbars_clean function to take fig, main_ax, and mapobj arguments
    * These are passed directly through to imagery_windbarbs.py output_clean_windbarbs function
#### modified: geoips/interface_modules/procflows/single_source.py
* Support plotting data without producing output
    * Add "no_output" option to "plot_data" function - do not produce output files if set, only plot
* Support get_area_defs_from_command_line_args with METADATA only available
    * Make "variables" argument optional - currently unused anyway
#### modified: geoips/interface_modules/user_colormaps/pmw_tb/cmap_Rain.py
* Use colorbar_kwargs and set_ticks_kwargs options for demonstration purposes
    * Same functionality as previously, just using explicit keyword argument specifications

## GEOIPS#104: 2022-10-21, VIIRS reader bug-fix for terminator case

### Bug fixes
* **geoips/interface_modules/readers/viirs_netcdf.nc**
    * Move VIIRS solar reflective bands to neww data_type:
        * MOD-Vis: M01, M02, M03, M04, M05, M06, M09
        * IMG-Vis: I01, I02, I03
        * These reflective bands are not present in nighttime granules,
         and causes issues when dealing with a pair of granules that cross the terminator.
    * Reader now capable of reading geo fields from a single file into multiple datasets

## GEOIPS#98: 2022-09-28, use 'conda-forge' vs 'defaults'
### Installation
* **setup.sh**: default to '-c conda-forge', allow '-c defaults' by request for conda commands:
    * **setup.sh conda_install**: use Miniforge by default, Miniconda if "conda_defaults_channel" passed
    * **setup.sh conda_update**: Use conda-forge by default, "defaults" if "conda_defaults_channel" passed
    * **setup.sh create_geoips_conda_env**: Use conda-forge by default, "defaults" if "conda_defaults_channel" passed
    * **setup.sh install**: matplotlib and cartopy still must use conda-forge
        * Remove version specifications for matplotlib and cartopy (allow latest until test outputs break)
* **setup.py**: Update versions to allow latest, but maintain specifically pre-installed versions
    * base: matplotlib>=3.5.3 (CI/CD installation requires 3.5.3 to work with cartopy)
    * base: shapely>=1.8.2 (CI/CD installation requires specific 1.8.2 build)
    * base: cartopy>=0.20.3 (CI/CD installation requires 0.20.3 to work with shapely)
    * test_outputs: matplotlib>=3.6.0 (update outputs to latest)
    * test_outputs: cartopy>=0.21.0 (update outputs to latest)
    * cicd_pipeline: Add specific matplotlib (3.5.3), cartopy (0.20.3), and shapely (1.8.2 pre-built) versions
        * This is NOT called from default interactive installation
* **README.md**
    * Update GEOIPS_ACTIVE_BRANCH to dev for NRLONLY
    * add GEOIPS_PACKAGES_DIR, GEOIPS_TESTDATA_DIR, and GEOIPS_DEPENDENCIES_DIR env vars for completeness
        * Do not use GEOIPS_BASEDIR within README EXCEPT to set above env vars
    * Pass "conda-forge" to base_install_and_test.sh to explicitly request "conda-forge" channel
* **base_install_and_test.sh**
    * Pass $conda_channel to setup.sh commands: conda_install, conda_update, create_geoips_conda_env
    * Separate update_conda and create_geoips_conda_env steps


# v1.5.2: 2022-09-26, testing updates, interp fixes, update xrdict outputs

### Bug fixes
* Force cartopy==0.20.3, matplotlib==3.5.3
    * cartopy 0.20.3 incompatible with matplotlib 3.6.0
    * cartop 0.21.0 works with 3.6.0, but incompatible with some proj libraries
* Remove instances of xarray.ufuncs.logical_and
    * No longer available at least as of v2022.06 (was available < 0.19.0)
    * Use numpy.logical_and instead
* **tests/outputs/smap.unsectored.text_winds/smap-spd_rss_smap_surface_winds_20210926.0000.txt.gz**
    * Add SMAP output file back in (accidentally deleting with previous commit)
* **geoips/interface_modules/readers/gmi_hdf5.py**
    * Sort original_source_filenames so consistent order in YAML metadata outputs

## GEOIPS#95: 2022-09-26, add additional information for netcdf diff output
### Testing Improvements
* modified: **geoips/compare_outputs.py**
    * When assert_allclose or assert_identical fail, include min/max/mean diff information in log output
    * assert_allclose output limited.

## GEOIPS#92: 2022-09-21, update ASCAT UHR reader and products
### Major New Functionality
* modified: **geoips/interface_modules/readers/ascat_uhr_netcdf.py**
    * Use _B_ and _C_ in filenames to determine METOP-B vs METOP-C
    * Use updated filename format for storm name and date MUIFA_20220911_19947_C_D-product.nc
    * DO NOT subtract 90 from latitude
    * Use single "sig" variable rather than sig_fore and sig_aft
    * Use time array, and temporarily use YYYYMMDD from filename for units (bug upstream)
* modified: **geoips/yaml_configs/product_inputs/ascatuhr.yaml**
    * Add sectored and unsectored text outputs
* modified: **geoips/yaml_configs/product_inputs/ascat.yaml**
    * Add sectored and unsectored text outputs
* UNMODIFIED: **geoips/yaml_configs/sectors_dynamic/tc_web_ascatuhr_barbs_template.yaml**
* new file: **geoips/yaml_configs/sectors_dynamic/tc_huge/tc_0p1km_3200x3200.yaml**
    * 100m resolution, 3200x3200, useful for zoomed in wind barbs.
* new: **geoips/yaml_configs/plotting_params/gridlines/tc_0p25degree.yaml**
    * Add quarter degree gridlines - useful for zoomed in windbarbs plots

## GEOIPS#90: 2022-09-21, expand error handling in overpass predictor
### Bug fixes
* **geoips/sector_utils/overpass_predictor.py**
    * Add handling for TypeError when calculating the next overpass

## GEOIPS#84: 2022-09-13, update image comparison fuzz from 1% to 5%
### Installation and Testing
* **geoips/compare_outputs.py**: update image comparison fuzz from 1% to 5%

## GEOIPS#84: 2022-09-13, update xrdict output formats
### Refactor
* **geoips/dev/output.py**: consolidate xarray_dict based output format families
    * 'xarray_dict_to_image' -> 'xrdict_area_varlist_to_outlist'
    * 'xarray_dict_data' -> 'xrdict_varlist_outfnames_to_outlist'
    * 'xarray_dict' -> 'xrdict_product_outfnames_to_outlist'
    * xarray_datasets -> xarray_dict
    * xarray_objs -> xarray_dict
* **geoips/interface_modules/procflows/single_source.py**: update output format if statements for xarray_dict-based
	* xarray_dict_data -> xrdict_varlist_outfnames_to_outlist
	* xarray_dict -> xrdict_area_product_outfnames_to_outlist
	* make product_name_title and mpl_colors_info optional for xrdic_area_product_outfnames_to_outlist family
* **geoips/interface_modules/output_formats/text_winds.py**: Update for xarray_dict-based standards
	* xarray_dict_data -> xrdict_varlist_outfnames_to_outlist
	* xarray_objs -> xarray_dict
	* product_names -> varlist

## GEOIPS#86: 2022-09-13, update image comparison fuzz from 1% to 5%
### Installation and Testing
* **geoips/compare_outputs.py**: update image comparison fuzz from 1% to 5%

## GEOIPS#80: 2022-09-12, add "force_alt_varname" to coverage checks
### Improvements
* Add "force_alt_varname" option to coverage checks to force using alt_varname_for_coverage
    * modified: **geoips/interface_modules/coverage_checks/center_radius.py**
    * modified: **geoips/interface_modules/coverage_checks/center_radius_rgba.py**
    * modified: **geoips/interface_modules/coverage_checks/masked_arrays.py**
    * modified: **geoips/interface_modules/coverage_checks/numpy_arrays_nan.py**
    * modified: **geoips/interface_modules/coverage_checks/rgba.py**

## GEOIPS#82: 2022-09-13, add shared uncompress_test_data script
### Major New Functionality
* **tests/utils/uncompress_test_data.sh**
    * Utility that will decompress gz, bz2, or tgz data files within the passed directory
    * This can be used by individual repos to decompress their test and output data files prior to processing
    * This script is not called automatically - must be called by the individual repo's uncompress_test_data.sh

## GEOIPS#78: 2022-09-10, resolve missing lat/lon issues in interp
### Bug fixes
* **geoips/interface_modules/interpolation/pyresample_wrappers/interp_gauss.py**
* **geoips/interface_modules/interpolation/pyresample_wrappers/interp_nearest.py**
* **geoips/interface_modules/interpolation/scipy_wrappers/interp_grid.py**
    * If "output_xarray" is None, intiialize to xarray.Dataset()
    * If 'latitude' is not in output_xarray.variables, then calculate and add all geolocation information to Dataset
        * This allows passing an empty xarray Dataset OR None for output_xarray, and still having proper functionality

## GEOIPS#29: 2022-09-09, allow copying files when checking file list
### Installation and Test
* **tests/utils/check_output_file_list.sh**
    * If "copy_dir" is specified, copy files to appropriate location
    * subdirectory based on extension
    * "noext" subdirectory if no "." in filename
    * gunzip and rename files to ".tif" if ".jif.gz" extension
    * Also include original .gz file separately from unzipped version
* **tests/utils/get_realtime_test_args.sh**
    * Provide common args for realtime test script setup, so if they need updated, they will be in one place.

## GEOIPS#75: 2022-09-07, 1.5.2 bug fixes and updates
### Installation and Test
* **base_install_and_test.sh**: Remove seviri, vim8, vim8_plugin, and natural-earth-vector setup comments
### Bug fixes
* **geoips/interface_modules/procflows/single_source.py**
    * Move "copy_standard_metadata" after interpolation, before calling algorithm
    * Previously True Color algorithm was failing due to missing "source_name" attribute on xarray Dataset.
* **geoips/interface_modules/procflows/config_based.py**
    * Skip background data if no coverage (do not fail catastrophically)
* **geoips/interface_modules/readers/utils/geostationary_geolocation.py**
    * Raise "CoverageError" if there are no good_lines or good_samples

## GEOIPS#5: 2022-09-09, for drop_nan, include lat/lon if masked
### Bug fixes
* **geoips/interface_modules/interpolation/pyresample_wrapper/interp_gauss.py**
    * If "drop_nan=True" ensure lat/lon masking is included in the overall mask.


# v1.5.2.dev2: 2022-09-02, image_utils numpy docstrings, basic CI

## NRLMMD-GEOIPS/geoips#17: 2022-08-12, add non-member forking info to git-workflow
### Documentation
* **docs/git-workflow.rst**
    * Add non-member forking process
    * Note under branching instructions that branching only applies to members of NRLMMD-GEOIPS, non-members must follow forking instructions

## NRLMMD-GEOIPS/geoips#29: 2022-08-28, Update image_utils to numpy docstrings
### Documentation
* Update image_utils directory for proper numpy style docstrings
    * **geoips/image_utils/__init__.py**
    * **geoips/image_utils/colormap_utils.py**
    * **geoips/image_utils/maps.py**
    * **geoips/image_utils/mpl_utils.py**
* **geoips/compare_outputs.py** Update imagemagick compare metric from rmse to ae + fuzz 1%

## NRLMMD-GEOIPS/geoips#34 - 2022-08-12 - Add Dockerfile and Basic CI
### Installation and Test
* **.dockerignore**
  * Add .dockerignore
* **.github/workflows/build-and-test-in-docker.yaml**
  * Add a basic workflow that builds a docker images and pushes it to the GitHub package registry
* **Dockerfile**
  * Add a dockerfile that builds an image containing a working version of GeoIPS
* **base_install_and_test.sh**
  * Remove conda_link step
  * Directly source bashrc
* **geoips/filenames/base_paths.py**
  * Add `BASE_PATH` to `PATHS{}` and collect it using `pathjoin(dirname(__file__), '..')`
  * Remove `PATHS['GEOIPS']`
  * Use `BASE_PATH` to find `TC_TEMPLATE` path
* **geoips/image_utils/maps.py**
  * Add some debug statements
* **geoips/interface_modules/title_formats/__init__.py**
  * Add an __init__.py here so this can be imported correctly
* **geoips/interface_modules/user_colormaps/tpw/tpw_cimss.py**
  * Use `BASE_PATH` rather than `GEOIPS`
* **geoips/interface_modules/user_colormaps/tpw/tpw_purple.py**
  * Use `BASE_PATH` rather than `GEOIPS`
* **geoips/interface_modules/user_colormaps/tpw/tpw_pwat.py**
  * Use `BASE_PATH` rather than `GEOIPS`
* **geoips/utils/__init__.py**
  * Add an __init__.py here so this can be imported correctly
* **setup.py**
  * Add use of `package_data` for yaml_configs and image_utils/ascii_palettes
  * Allow pip install of pyshp, shapely, and cartopy
  * Move install of pyshp from `test_outputs` to main `install_requires`
* **setup.sh**
  * Add creation of `$GEOIPS_DEPENDENCIES_DIR/bin` at top of script
  * Remove `conda_link` action
  * Directly call `conda init` rather than `$BASECONDAPATH/conda init` (assumes conda is in $PATH) from sourcing either
    ~/.bashrc or setup/config_geoips
  * Use `GEOIPS_TESTDATA_DIR` rather than `$GEOIPS_PACKAGES_DIR/geoips/tests/data/`
* **tests/scripts/abi.static.Infrared.imagery_annotated.sh**
  * Replace all references to `GEOIPS/tests/data/` with `GEOIPS_TESTDATA_DIR`
* **tests/scripts/abi.static.Visible.imagery_annotated.sh**
  * Replace all references to `GEOIPS/tests/data/` with `GEOIPS_TESTDATA_DIR`
* **tests/scripts/amsr2_ocean.tc.windspeed.imagery_clean.sh**
  * Replace all references to `GEOIPS/tests/data/` with `GEOIPS_TESTDATA_DIR`
* **tests/scripts/documentation_imagery.sh**
  * Replace all references to `GEOIPS/tests/data/` with `GEOIPS_TESTDATA_DIR`
* **tests/yaml_configs/abi_test_low_memory.yaml**
  * Replace all references to `GEOIPS/tests/data/` with `GEOIPS_TESTDATA_DIR`
* **tests/yaml_configs/abi_test.yaml**
  * Replace all references to `GEOIPS/tests/data/` with `GEOIPS_TESTDATA_DIR`

## GEOIPS#7: 2022-08-30, support data_fusion
### Refactor
* **geoips/dev/product.py**: Replace "base_product_name" with "product_template" in get_product
    * product_name: Actual name of current product
    * product_template: YAML file to use as the base for the current product
    * product_category: A specification that allows grouping "similar" products
      (ie, 37H, 34H, 36H all in the 37H "product_category")
### Major New Functionality
* **geoips/yaml_configs/product_params/alg.yaml**: Template containing:
    * product_type='alg'
* **geoips/yaml_configs/product_params/interp.yaml**: Template containing:
    * product_type='interp'
    * interp_func default: pyresample_wrappers.interp_nearest
    * interp_args default: {}
* **geoips/yaml_configs/product_params/unmodified.yaml**: Template containing:
    * product_type='unmodified'
* **tests/sectors/tc_bdecks/bep072022.dat**
    * EP07Frank sample bdeck file
### Improvements
* **geoips/interface_modules/procflows/single_source.py**: Support data_fusion functionality
    * **def pad_area_definition**
        * Allow passing "force_pad" for non-TC sectors
        * Allow passing x_scale_factor and y_scale_factor for different scaling factors
    * **def plot_data**: Support xarray_dict output format type.
    * **def get_alg_xarray**: Support data_fusion processing
        * If variable_names is passed, use it (impacts reader_defined and self_registered products)
        * set "alg_func_type" to None if no algorithm defined.
        * Default "interp_xarray" to xarray.Dataset() rather than None
        * Reassign interp_func within the interpolation loop, to ensure it is using the current sect_xarray source
          for definiing the appropriate interpolation routine.
        * If "time" is contained in sect_xarray dims, interpolate each slice of the array separately
        * Copy standard metadata to "interp_xarray" before returning, using "force=False"
* **geoips/dev/utils.py**
    * Add "force" option to copy_standard_metadata - allow NOT replacing existing fields.
    * This will not impact existing functionality - default is force=True, and when force=True the original
      if statement will always be used.
* **geoips/geoips_utils.py**
    * Pass "force" option directly through to dev.utils.copy_standard_metadata


## GEOIPS#65: 2022-08-20, allow drop_nan option for interp_gauss
### Improvements
* **geoips/interface_modules/pyresample_wrappers/interp_gauss.py**
    * If drop_nan=True passed, remove all values from lat/lon/data arrays where any array contains numpy.nan
    * If drop_nan=False, operation remains unchanged (backwards compatible)

## GEOIPS#63: 2022-08-20, allow specifying base_product_name within product_inputs
### Major New Functionality
* **geoips/dev/product.py**: Use base_product_name if specified in product_inputs dict for retrieving product params
    * This allows specifying new product names directly within the product_inputs YAMLs, rather than
        requiring a separate YAML file for every product name.
    * Useful for classes of products that have all the same parameters, except potentially a different filename /
        required variable (ie, 34GHz, 35GHz, 36GHz and 37GHz products can now reuse the same 37H product, but have
        unique filenames)

## GEOIPS#65: 2022-08-20, generalized NOAA AWS download script
### Major New Functionality
* **setup.sh**: Update setup_abi_test_data to use download_noaa_aws.sh script.
* **tests/download_noaa_aws.sh**: Allows downloading specific satellite, YYYYMMDD.HHMN of data from NOAA AWS.
* **tests/scripts/abi.static.Infrared.imagery_annotated.sh**: Update GOES16 path to use $GEOIPS_TESTDATA_DIR
* **tests/scripts/abi.static.Visible.imagery_annotated.sh**: Update GOES16 path to use $GEOIPS_TESTDATA_DIR
* **tests/scripts/documentation_imagery.sh**: Update GOES16 path to use $GEOIPS_TESTDATA_DIR
* **tests/yaml_configs/abi_test.yaml**: Update GOES16 path to use $GEOIPS_TESTDATA_DIR
* **tests/yaml_configs/abi_test_low_memory.yaml**: Update GOES16 path to use $GEOIPS_TESTDATA_DIR

## GEOIPS#62: 2022-08-21, new plugin process
### Documentation
* **docs/setup-new-plugin.rst**: Process for setting up a new test date repo, and plugin repo.
* **docs/version_control_templates.rst**: Remove rst - these are now direct GitHub templates.
* **docs/geoips_index.rst**: Remove version_control_templates.rst, add git-workflow and setup-new-plugin

## GEOIPS#57: 2022-08-17, support CARTOPY_DATA_DIR
### Installation and Test
* **setup.sh**: Link cartopy data into $CARTOPY_DATA_DIR vs ~/.local/share/cartopy
* **config_geoips**: Set CARTOPY_DATA_DIR to $GEOIPS_DEPENDENCIES_DIR/CARTOPY_DATA_DIR
* **setup.py**: Add shapely, cartopy, and pyshp requirements. cartopy error if not specified.


## GEOIPS#59: 2022-08-18, allow less strict image comparisons
### Improvements
* **geoips/compare_outputs.py**
    * Add "fuzz" argument to "images_match" function - default to 1%
    * Add "fuzz" argument to imagemagick compare call
    * Change metric from rmse to ae (RMSE did not appear to care about the fuzz factor)
    * Re-run compare with RMSE and no fuzz factor if test passes (to track differences)


# v1.5.2.dev1: 2022-08-16, improve install, test, and git workflow

## NRLMMD-GEOIPS/geoips#31 - add test datasets to .gitignore

### Improvements
* **geoips/.gitignore**
    * Add tests/data/** to .gitignore so they no longer appear in git status

## NRLMMD-GEOIPS/geoips#25 - add low_bandwidth option

### Installation and Test
* **README.md** - Pass low_memory and low_bandwidth options to base_install_and_test.sh
* **setup.sh** - Support low_bandwidth option for setup_abi_test_data (only download B14), and install (pip install minimum packages for tests)
* **base_install_and_test.sh** - Pass "low_bandwidth" option through to setup.sh

## NRLMMD-GEOIPS/geoips#27

### Installation and Test
* Add "check_system_requirements.sh" script to ensure system requirements are installed
    * git lfs
    * imagemagick
    * wget
    * recent git version

## NRLMMD-GEOIPS/geoips#17 - Update Git Workflow

### Documentation Updates

* **docs/git-workflow.rst**
    * Remove manual labeling on Issues
    * Remove manual labeling on PRs
    * Remove manual branching command line
    * Note that branches MUST be created via the Issue->Development->Create Branch option
    * Remove manual status updates on Project (should be automated via PRs linked to Issue)

## NRLMMD-GEOIPS/geoips#22 - Remove rclone.conf link to ~/.config/rclone

### Installation and Test
* **setup.sh**
    * Update setup_rclone command to remove the link from $GEOIPS_PACKAGES_DIR/geoips/setup/rclone_setup/rclone.conf
        to ~/.config/rclone/rclone.conf
    * Update setup_abi_test_data command to use explicit
        --config $GEOIPS_PACKAGES_DIR/geoips/setup/rclone_setup/rclone.conf
        argument rather than relying on default ~/.config/rclone/rclone.conf configuration

## NRLMMD-GEOIPS/geoips#15 - Add low memory options for base install tests

### Test Repo Updates
* abi.config_based_output_low_memory.sh
    * abi.static.Infrared.imagery_annotated png output
    * abi.tc.Infrared.imagery_annotated png and YAML metadata output
    * abi.tc.IR-BD.imagery_annotated png and YAML metadata output
* abi.static.Infrared.imagery_annotated.sh
    * abi.static.Infrared.imagery_annotated png output
* amsr2.config_based_overlay_output_low_memory.sh
    * amsr2.global_overlay.37pct.imagery_annotated_over_Infrared-Gray png and YAML metadata output
    * amsr2.global_overlay.89pct.imagery_annotated_over_Infrared-Gray png and YAML metadata output
    * amsr2.tc_overlay.37pct.imagery_annotated_over_Infrared-Gray png and YAML metadata output
    * amsr2.tc_overlay.89pct.imagery_annotated_over_Infrared-Gray png and YAML metadata output
* UPDATE outputs amsr2.config_based_overlay_output.sh (outputs were not previously included)
    * amsr2.global_overlay.37pct.imagery_annotated_over_Visible png and YAML metadata output
    * amsr2.global_overlay.89pct.imagery_annotated_over_Visible png and YAML metadata output
    * amsr2.tc_overlay.37pct.imagery_annotated_over_Visible png and YAML metadata output
    * amsr2.tc_overlay.89pct.imagery_annotated_over_Visible png and YAML metadata output

### Installation and Test
* **base_install_and_test.sh**
    * Add "low_memory" option that allows testing Infrared-only ABI rather than Visible.
        ~4GB vs ~12GB memory requirement.

### Bug fixes
* **amsr2.config_based_overlay_output.sh**
    * Un-indent "backgrond_products" so background imagery is included in outputs
    * Add outputs to comparison directories

## NRLMMD-GEOIPS/geoips_tutorial#3 - Add AMSR2 test data and test scripts to base install and test

### Installation and Test
* **README.md**
    * Add git lfs install to setup, to ensure Large File Storage tracked data files are cloned properly
* **base_install_and_test.sh**
    * Add clone of test_data_amsr2
    * Add AMSR2 test: $GEOIPS_PACKAGES_DIR/geoips/tests/scripts/amsr2.config_based_overlay_output.sh
* **setup.py**
    * Add scikit-image to "coverage_checks" section of install_requires
* **config_geoips**
    * Add git lfs install, for redundancy
    * Add GEOIPS_TESTDATA_DIR environment variable, to allow non-GEOIPS_BASEDIR test data locations.
* **AMSR2 Test Scripts**
    * Add AMSR2 config based test script: tests/scripts/amsr2.config_based_overlay_output.sh
    * Add AMSR2 YAML output config: tests/yaml_configs/amsr2_test.yaml
        * 89pct and 37pct output products
        * TC-centric sector
        * Global sector
        * Visible AHI background imagery

## NRLMMD-GEOIPS/geoips#6,8,9,11 - Streamline installation process, support Mac installation

### Installation and Test
* **base_install_and_test.sh**
    * Exit immediately if GEOIPS_BASEDIR or GEOIPS_REPO_URL are not defined
    * Comment out several sections of installation, to reduce time and disk space
        * natural-earth-vector data download (will rely on latest shapefiles during cartopy processing)
        * natural-earth-vector linking to ~/.local/share/cartopy
            * Will NOT reinstate this step - cartopy supports CARTOPY_DATA_DIR as of 6 August 2021
        * vim8 installation (only for use of vim8 plugins to help with following style guides)
        * vim8 plugin installation
        * seviri setup
    * Remove BASECONDAPATH from conda cartopy installation (conda will be in PATH)
* **setup.sh**
    * To support Mac installations, use "uname -m" when determining filenames for
        rclone and miniconda3 installation
    * Rather than sourcing `.bashrc` to get the conda environment set up, source `geoips_conda_init_setup`.
* **geoips_conda_init_setup**
    * To support Mac installations, use $(conda shell.bash activate geoips_conda) when activating
        conda vs "conda geoips_conda activate"
    * Allow use of GeoIPS-specific conda installation along-side user/system level installation where
      the user/system level installation may be initialized in `.bash_profile`. Uses GeoIPS-specific
      installation by default, if it is found.
* **color_prompt**
    * Add "$CONDA_PROMPT_MODIFIER" to $PS1
* **repo_clone_update_install.sh**
    * If GEOIPS_TESTDATA_DIR, GEOIPS_PACKAGES_DIR, or GEOIPS_DEPENDENCIES_DIR are set, use those,
        otherwise default to placing under $GEOIPS_BASEDIR
    * Update default branch from dev to main
* **README.md**
    * Update github.com GEOIPS_ACTIVE_BRANCH from dev to main
* **setup.sh**
    * Update default branches from dev to main


# v1.5.1: 2022-07-13, fix overpass error handling, fix ticklabels error, add area_def_adjuster outputs, update test rm

### Improvements
* **config_based final outputs**
    * Add output filenames from area\_def\_aduster call to final\_products
    * NOTE: area\_def\_adjuster outputs NOT included in single\_source processing - it must be explicitly requested
        within YAML output config - not explicitly requested in single_source command line call, so not supported
        to include via single_source processing.
* **metadata_default output format**
    * Allow optional "include\_metadata\_filename" kwarg (default False for backwards compatibility)
        * Helpful for confirming metadata is going to the expected output location!
* **config-based metadata YAML kwargs specifications**
    * Update so metadata YAML kwargs are specified in the YAML output config using "metadata\_filename\_format" rather
        than "filename_format"

### Documentation Updates
* Update \*.md Distro statement headers to use 4 spaces prefix rather than ### (formatting improvement)

### Bug fixes
* **tests/utils**
    * Go 3 levels deep for delete\_diff\_dirs.sh and delete\_files\_from\_repo.sh
        * Allow additional levels for test output directories, for better organization.
* **overpass predictor**
    * Add handling for AttributeErrors encountered under overpass\_predictor.calculate\_overpass
    * Replace print statements with logger, and show which satellite has the bad overpass prediction
* **image_utils.mpl_utils**
    * Do not try to set cbar.set\_ticklabels unless cmap\_ticklabels exists
* **metadata_tc**
    * remove unused fname argument from update\_sector\_info\_with\_default\_metadata call signature
* **gmi.tc.89pct.imagery_clean.sh**
    * Update gmi 89pct test to use tc\_clean\_fname rather than tc\_fname


# v1.5.0: 2022-06-09, consolidate/update test outputs to latest dependencies, geoips2->geoips, update GEOIPS\_REPO\_URL

### v1.5.0post2: 2022-06-16, update to github.com/NRLMMD-GeoIPS

#### Bug fixes
* **Installation and test**
    * Replace github.com/U-S-NRL-Marine-Meteorology-Division with github.com/NRLMMD-GeoIPS
        * git-workflow.rst
        * installation.rst
        * README.md
        * config_geoips

### v1.5.0post1: 2022-06-11, support \<ORG>/\<REPO> specifications

#### Improvements
* **setup.sh repository name specifications**
    * "\<repo\_name>" - $GEOIPS\_BASE\_URL/GEOIPS/\<repo\_name>.git == $GEOIPS\_REPO\_URL/\<repo\_name>.git
    * "\<repo\_org\>/\<repo\_name>" - $GEOIPS\_BASE\_URL/\<repo\_org\>/\<repo\_name>.git
    * "/\<repo\_name>" - $GEOIPS\_BASE\_URL/\<repo\_name>.git
* **Remove .github/hooks/update.ry - unused**

### Test Repo Updates
* **Test Sectors**
    * Add bdeck files
        * bwp012020.dat
        * bep112021.dat
        * bsh082021.dat
* **Additional direct test calls and outputs**
    * ATMS 165H reprojected netcdf output, bep112021
        * Test script: $GEOIPS/tests/scripts/atms.tc.165H.netcdf_geoips.sh
        * Output dir: $GEOIPS/tests/outputs/atms.tc.165H.netcdf_geoips
    * EWS-G Infrared reprojected clean imagery, ewsg.yaml
        * Test script: $GEOIPS/tests/scripts/ewsg.static.Infrared.imagery_clean.sh
        * Output dir: $GEOIPS/tests/outputs/ewsg.static.Infrared.imagery_clean
    * SAPHIR 183-3HNearest reprojected annotated imagery, bsh192021
        * Test script: $GEOIPS/tests/scripts/saphir.tc.183-3HNearest.imagery_annotated.sh
        * Output dir: $GEOIPS/tests/outputs/saphir.tc.183-3HNearest.imagery_annotated
    * AMSR2 OCEAN windspeed clean imagery output
        * Test script: $GEOIPS/tests/scripts/amsr2_winds.tc.windspeed.imagery_clean.sh
        * Output dir: $GEOIPS/tests/outputs/amsr2_winds.tc.windspeed.imagery_clean
    * ASCAT METOP-C Low resolution (25km) windbarb annotated imagery output
        * Test script: $GEOIPS/tests/scripts/ascat_low_knmi.tc.windbarbs.imagery_windbarbs.sh
        * Output dir: $GEOIPS/tests/outputs/ascat_low_knmi.tc.windbarbs.imagery_windbarbs
    * SSMI 37pct clean imagery output
        * Test script: $GEOIPS/tests/scripts/ssmi.tc.37pct.imagery_clean.sh
        * Output dir: $GEOIPS/tests/outputs/ssmi.tc.37pct.imagery_clean
    * TPW MIMIC fine, TPW-PWAT product annotated imagery output
        * Test script: $GEOIPS/tests/scripts/mimic_fine.tc.TPW-PWAT.imagery_annotated.sh
        * Output dir: $GEOIPS/tests/outputs/mimic_fine.tc.TPW-PWAT.imagery_annotated
* **Updated test scripts**
    * ahi.IR-BD.imagery\_clean.sh -> ahi.WV.geotiff.sh
* **Update test script names to include sector type**
    * abi.Visible.imagery\_annotated.sh ->                  abi.static.Visible.imagery\_annotated
    * ahi.WV.geotiff.sh ->                                  ahi.tc.WV.geotiff.sh
    * amsr2.89H-Physical.imagery\_annotated.sh ->           amsr2.tc.89H-Physical.imagery\_annotated.sh
    * amsub\_mirs.tc.183-3H.imagery\_annotated ->           amsub\_mirs.tc.183-3H.imagery\_annotated.sh
    * ascat\_uhr.wind-ambiguities.imagery\_windbarbs.sh ->  ascat\_uhr.tc.wind-ambiguities.imagery\_windbarbs.sh
    * ascat\_knmi.windbarbs.imagery\_windbarbs\_clean.sh -> ascat\_knmi.tc.windbarbs.imagery\_windbarbs\_clean.sh
    * atms.165H.netcdf\_geoips.sh ->                        atms.tc.165H.netcdf\_geoips.sh
    * ewsg.Infrared.imagery\_clean.sh ->                    ewsg.static.Infrared.imagery\_clean.sh
    * gmi.89pct.imagery\_clean.sh ->                        gmi.tc.89pct.imagery\_clean.sh
    * imerg.Rain.imagery\_clean.sh ->                       imerg.tc.Rain.imagery\_clean.sh
    * oscat\_knmi.windbarbs.imagery\_windbarbs.sh ->        oscat\_knmi.tc.windbarbs.imagery\_windbarbs.sh
    * hy2.windspeed.imagery\_annotated.sh ->                hy2.tc.windspeed.imagery\_annotated.sh
    * mimic.TPW\_CIMSS.imagery\_annotated ->                mimic\_coarse.static.TPW-CIMSS.imagery\_annotated.sh
    * sar.nrcs.imagery\_annotated.sh ->                     sar.tc.nrcs.imagery\_annotated.sh
    * smos.sectored.text\_winds ->                          smos.tc.sectored.text\_winds.sh
    * viirsday.Night-Vis-IR.imagery\_annotated.sh->         viirsday.tc.Night-Vis-IR.imagery\_annotated.sh
    * viirsmoon.Night-Vis-GeoIPS1.clean.sh ->               viirsmoon.tc.Night-Vis-GeoIPS1.imagery\_clean.sh
* **Update test output directories to include sector type and output type**
    * abi\_Visible\_image ->                   abi.static.Visible.annotated
    * ahi\_IR-BD ->                            ahi.tc.WV.geotiff
    * amsr2\_89H-Physical ->                   amsr2.tc.89H-Physical.imagery\_annotated
    * amsub\_183-3H ->                         amsub\_mirs.tc.183-3H.imagery\_annotated
    * ascat\_uhr\_wind-ambiguities ->          ascat\_uhr.tc.wind-ambiguities.imagery\_windbarbs
    * ascat\_knmi\_windbarbs ->                ascat\_knmi.tc.windbarbs.imagery\_windbarbs\_clean
    * atms\_165H ->                            atms.tc.165H.netcdf\_geoips
    * ewsg\_Infrared ->                        ewsg.static.Infrared.imagery\_clean
    * gmi\_89pct ->                            gmi.tc.89pct.imagery\_clean
    * hy2\_windspeed ->                        hy2.tc.windspeed.imagery\_annotated
    * imerg\_Rain ->                           imerg.tc.Rain.imagery\_clean
    * mimic\_TPW\_CIMSS ->                     mimic\_coarse.static.TPW-CIMSS.imagery\_annotated
    * modis\_Infrared ->                       modis.Infrared.unprojected\_image
    * oscat\_knmi\_windbarbs ->                oscat\_knmi.tc.windbarbs.imagery\_windbarbs
    * sar\_nrcs ->                             sar.tc.nrcs.imagery\_annotated
    * smap\_text\_winds ->                     smap.unsectored.text\_winds
    * smos\_sectored ->                        smos.tc.sectored.text\_winds
    * seviri\_WV-Upper ->                      seviri.WV-Upper.unprojected\_image
    * ssmis\_color89 ->                        ssmis.color89.unprojected\_image
    * viirsclearnight\_Night-Vis-IR-GeoIPS1 -> viirsclearnight.Night-Vis-IR-GeoIPS1.unprojected\_image
    * viirsday\_Night-Vis-IR ->                viirsday.tc.Night-Vis-IR.imagery\_annotated
    * viirsmoon\_Night-Vis-GeoIPS1 ->          viirsmoon.tc.Night-Vis-GeoIPS1.imagery\_clean
* Added TC bdeck files
    * bal052021.dat (SAPHIR test case, unused)
    * bal032020.dat (SAR test cases, unused)
    * bwp252021.dat (SAR test cases, unused)
    * bsh242020.dat (SEVIRI test case)
* **ABI config-based test script**
    * Update to standard \<sensor>.\<sector\_type>.\<product>.\<output\_type> directory format
    * Update YAML metadata to use sectors/tc\_bdecks sector path
* **Dependency Version Update**
    * matplotlib 3.4.3->3.5.2
    * cartopy 0.20.0 -> 0.20.2
    * pyshp 2.1.3 -> 2.2.0
    * natural-earth-vector 5.0.0 -> 5.2.0
    * Impacted test outputs
        * amsub_mirs.tc.183-3H.imagery_annotated
        * ascat_low_knmi.tc.windbarbs.imagery_windbarbs
        * hy2.tc.windspeed.imagery_annotated
        * mimic_coarse.static.TPW-CIMSS.imagery_annotated
        * mimic_fine.tc.TPW-PWAT.imagery_annotated
        * oscat_knmi.tc.windbarbs.imagery_windbarbs
        * saphir.tc.183-3HNearest.imagery_annotated
        * sar.tc.nrcs.imagery_annotated
        * AFTER TEST DATA UNCOMPRESS BUG FIX: amsr2.tc.89H-Physical.imagery_annotated
        * AFTER TEST DATA UNCOMPRESS BUG FIX: ascat_uhr.tc.wind-ambiguities.imagery_windbarbs

### Refactor
* **File modifications**
    * Update all instances of 'geoips2' with 'geoips'
    * Update all instances of 'GEOIPS2' with 'GEOIPS'
    * Update GEOIPS\_REPO\_URL to github.com/NRLMMD-GeoIPS
* **File renaming**
    * Rename all files and directories containing 'geoips2' with \*geoips\*
* **Setup standardization**
    * Replace 'setup\_geoips2.sh install\_geoips2' with 'setup.sh install'
    * Replace all instances of 'setup\_geoips2.sh' with 'setup.sh'
* **Test sectors**
    * Organize test sectors for easier identification of available sectors,
        and easier expansion to additional sector types in the future.
        * static (currently large global and geostationary coverage sectors)
        * tc_bdecks (bdeck files only)
    * Update all test scripts and YAML configs for new test sector locations
    * Add tc\_bdeck files
        * bep062021.dat - used with ABI daytime test dataset
        * bwp192021.dat - Large WPAC storm 2021, Chantu (not currently used with any test datasets)
    * Update bep112021.dat - used with ATMS test script
        * File reprocessed April 2022 was of incorrect format for bdeck_parser - replace with last "realtime"
            bdeck file.
        * Probably need to eventually create new parser for reprocessed deck files.

### Major New Functionality
* **Product types**
    * Add 'alg\_interp\_cmap' product type to geoips/dev/product.py
    * Add 'interp' product type to geoips/dev/product.py
* **Algorithm / interpolation order in procflows**
    * Check explicit list of product types when attempting to pull "alg" from product
        * ['alg', 'alg_cmap', 'interp_alg', 'interp_alg_cmap', 'alg_interp_cmap']
    * Check explicit list of product types when attempting to apply algorithm prior to interpolation
        * ['alg_cmap', 'alg_interp_cmap', 'alg']
    * Check explicit lists of product types / algorithm types when attempting to apply the results of interpolation/
        algorithm application to the final xarray object
        * ['interp']:
            * Use interp_xarray unchanged as final xarray object
        * ['xarray_to_numpy']:
            * Pass entire "interp_xarray" to algorithm,
            * set returned numpy array as "product_name" variable
        * ['xarray_to_xarray']:
            * Pass entire "interp_xarray" to algorithm,
            * set entire returned xarray object as "interp_xarray"
        * ['single_channel', 'channel_combination', 'list_numpy_to_numpy', 'rgb']
            * Pass list of numpy arrays to algorithm.
            * Set returned numpy array to "product_name" variable in xarray object.
        * Anything else
            * Raise ValueError - must explicitly implement new types to work within procflow.
            * Previously we defaulted to list_numpy_to_numpy
            * If we do want a default, it should probably be "xarray_to_xarray", but for now we will leave it explicit.
* **Coverage checks**
    * Add kwarg to existing coverage checks allowing passing an alternative variable name to the coverage check,
        to be used in the event the primary variable name does not exist (useful when no "product_name" variable
        exists in the xarray object)
    * Allows passing explicitly variable name to use for coverage checks from "covg\_args" in product YAML specs.

### Improvements
* **Pre-receive Hook**
    * Added "update" pre-receive hook to allow git commit message format hooks before push to GitHub
        * Requires only one commit message in the current push to pass
            * Must include valid Issue ID (GEOIPS/<issue_repo_name>#<issue_num>)
            * Must follow format specification:
                * one summary line
                * one blank line (if more than one line in commit message)
                * OPTIONAL: additional lines with detailed information
* **ssmi_binary**
    * Raise sensible exception when incorrect data file passed into ssmi\_binary reader
* **TPW Products**
    * Update TPW product names to use '-' rather than '\_', to follow standard practice

### Documentation Updates
* **GitHub Workflow**
    * Add rst documentation for full GitHub workflow
        1. Creating Issue
        2. Making changes to repositories
        3. Pushing changes to GitHub
        4. Creating a Pull Request
* **CHANGELOG_TEMPLATE.md**
    * Add note at beginning that CHANGELOG\_TEMPLATE.md itself should *not* be modified.

### Bug fixes
* **ATMS Reader**
    * Add atms reader to setup.py
    * Update original\_source\_filenames to support multiple files in atms reader
* **SAPHIR Reader**
    * Replace h5\_dataset.value construct with h5\_dataset[...]


# v1.4.8: 2022-05-15, use consistent shapefiles, require CHANGELOG update for PR approval, GMI in documentation

### Documentation Updates
* **Pull Request Templates**
    * Note that updates to CHANGELOG are *required* prior to pull request approval.
    * Use CHANGELOG updates copy-pasted as the "Summary" section in the pull request.
    * Add template for pull request title (<ticket num> <repo name> <short description>
* **CHANGELOG_TEMPLATE.md**
    * Add template with appropriate headers, formatting, and categories for proper CHANGELOG.md updates.
* **Available functionality**
    * *GMI Reader Example*
        * documentation_imagery.sh: Added GMI global reprojected image call
        * available_functionality.rst: Added GMI reader section
        * docs/images: Added GMI global image output

### Bug fixes
* **Installation and test**
    * Add "cd natural-earth-vector" prior to checking out v5.0.0 cartopy shapefiles
        * v5.0.0 required in order for test outputs to match.


# v1.4.7: 2022-05-06, multiple coverage check types, ability to plot coverage outline, optional version requirements

### Major New Functionality
* **Add ability to plot coverage outline**
    * single_source.py procflow
        * Allow passing optional "output_dict" to output_format modules
    * imagery_annotated.py output_format
        * Allow checking for "plot_coverage" option in product params from imagery_annotated output format
    * center_radius.py coverage check module
        * Add "plot_coverage" function to center_radius coverage check module.
            * When "plot_coverage" is added to product params imagery_annotated will call this function to
                include the outline of the coverage check function. Add via:
                * in YAML product spec, or
                * command line "product_params_override", or
                * in YAML output config "product_params_override"
                    * imagery_annotated will call this function to include the outline of the coverage check function.

### Improvements
* **Update Coverage Checks to Allow filename, full, and image_production based checks**
    * Include fname, full, and image_production covg funcs in metadata_tc outputs
    * Use "fname_covg_func" rather than "covg_func" when setting coverage for filename
    * Use max of "fname_covg" and "image_production_covg" when testing for minimum coverage
* **Installation Updates**
    * Moving version requirements for efficiency improvements to extra_requires
        * Rather than forcing satpy>=0.33.1 and pyresample>=1.22.3, include as an extra
            "efficiency_improvements" package in setup.py
        * Then, install efficiency_improvements and test_outputs extras FIRST so those packages and dependencies are
            installed first if desired.
* **Duplicate File Removal**
    * For tc_fname format, rather than only checking coverage, now have a 3 tiered duplicate file check:
        * If file has < max_coverage, delete
        * If file has > min_dt, delete
        * If another file has already been matched, delete (this is random!)
* **Output Filenames**
    * If output_fname is None, do not add to list or attempt to create metadata filename
        * Allow filename_formats to return None. If invalid, just continue.
        * This allows specifying multiple filename formats, and skipping formats that are invalid.
* **Real-time processing**
    * config\_based.py
        * Moved product database writes to new write_to_database function

### Bug fixes
* **Real-time processing**
    * config\_based.py
        * Added two new calls to write_to_database function, that stores unsectored and sectored products to database (these were previously missed)


# v1.4.6: 2022-04-18, metadata\_tc, center\_radius\_rgba, coverage check info in metadata, real-time bug fixes

### Major New Functionality
* **Product Display**
    * Add "cbar\_label" kwarg to all passive microwave colormaps
        * Allows passing "cbar_lable" from product inputs and product params YAMLs
    * Add Coverage Function information
* **Coverage Checks**
    * Add center\_radius\_rgba coverage check
        * use arr[:, :, 3] alpha layer for masked values rather than arr.mask
* **Metadata YAML outputs**
    * Add new metadata\_tc output format
        * metadata_default will NOT change, for consistent general test outputs
        * Include coverage check function information within metadata_tc.
    * single\_source.py/config\_based.py
        * Allow passing "product_name" to metadata output format modules (via metadata_fname_dict kwarg)
            * This allows accessing information via "dev/product.py" interfaces for metadata outputs
* **Database Hooks**
    * Add hooks for accessing modules capable of generating and populating a database of product outputs during
        geoips processing
* **Command line arguments**
    * --product\_db\_writer: Controls interface module used to populate product database by single\_source procflow
    * --product\_db\_writer\_override: Adds ability to override database interface modules set under the
         available sectors in the output config file

### Improvements
* **Coverage Checks**
    * dev/product.py
        * allow alternate field name for coverage funcs in output config
        * Defaults to "covg_func" and "covg_args"
        * Pass "covg_args_field_name" to get_covg_args_from_product or get_covg_from_product to use alternative
            field name
        * This allows specifying multiple coverage check functions (ie, one for image_production and one for fnames)
    * single\_source.py/config\_based.py
        * Use "image_production_covg_*" when determining if there is sufficient coverage
            to generate an output product
            * Defaults to use "covg_func" if "image_production_covg_*" not defined
* **area_def_adjusters**
    * Support list\_xarray\_list\_variables\_to\_area\_def\_out\_fnames adjuster\_type
        * Allows returning list of output filenames, in addition to adjusted area def
        * Allows producing valid output products via an area_def_adjuster

### Bug fixes
* **Real-time processing**
    * Reduce tc\_fname remove duplicates search time from 10 min to 3 min
        * This was previously deleting geostationary products from consecutive collect times.
    * Update search time for matching dynamic sector times to -6h to +9h
        * ie, data can come up to 9h after sector time and still match given sector.
        * This allows for TC sector updates delayed up to 9h during real-time processing
* **Coverage Checks**
    * center\_radius coverage check
        * previously computed the circle based on radius in pixels rather than radius in km
        * Update so we convert radius in km to pixels prior to passing into center_radius coverage check.
            * radius_pixels = radius_km / res_km
            * Results in higher coverage for many products (with resolution > 1km)

### 1.4.6post1 Post Release Patch (2022-04-21)
* #### Bug fixes
    * Update cartopy map data pull to ensure v5.0.0 natural earth vector data (required for test outputs)


# v1.4.5: 2022-03-18, --compare_paths to --compare_path, add --output_file_list_fname, add GEOIPS_COPYRIGHT_ABBREVIATED

### Breaking Interface Changes
* **Command line argument updates**
    * Replaced --compare_paths with --compare_path in command line arguments
        * pass command_line_args to set_comparison_path - if "compare_path" is set in command_line_args,
            use that instead of individual compare_paths within output config
        * Eventually add support for "compare_paths_override" which will allow setting a different
            compare_path for each output_type via command line (dictionary based) - but for now all or nothing

### Major New Functionality
* **Testing Utilities**
    * Added compare_output_file_list.sh utility, for comparing a list of files with existence on disk (simpler
        output comparison test than actually comparing the contents of each output product).
* **Command line arguments**
    * Add --output_file_list_fname to command line args, support in config-based and single-source procflows
        * Allows specifying full path to file to store output filenames from current - quickly update
            output file lists for comparison purposes.
    * Add support for "filename_format_kwargs" command line option as well as "filename_formats_kwargs" output config.
* **Sectors**
    * New TC Templates
        * 2km 512x512
        * 2km 800x800
* **Product display**
    * **base_paths.py**: Add GEOIPS_COPYRIGHT_ABBREVIATED, for use in product titles.

### Improvements
* **compare_outputs.py**: Add gzip_product functionality
    * Ensure if we gunzip a product during output comparisons, after we run the comparison we re-zip the file.
        Clean up after ourselves, and leave things the way we found them.
* **unprojected_image.py**: Update so default for unprojected_image is NO savefigs_kwargs
    (empty dictionary, which means masked background, rather than default black background)
* **setup_geoips.sh**
    * Remove dependence on git v2.19.1 - cd to directories rather than using git -C
    * Explicitly use setup scripts in the following order:
        1. setup_<package>.sh install_<package>
        2. setup.sh install
        3. setup.py (uses pip install)
    * If plugin exists in $GEOIPS_BASEDIR/installed_geoips_plugins.txt, do not attempt to reinstall
        * Allows initializing installed_geoips_plugins at the beginning of system installation to avoid
            massive reinstallations of common geoips plugin dependencies.

### Documentation Updates
* Formatting changes
    * correct spacing for code blocks and bullets
    * Remove level 4 header from "Available modules" and "Example outputs" in available functionality
* modis from 600 to 200 width
* Updated AMSU-A, AMSU-B, MHS comments for accuracy (MHS == AMSU-B, AMSU-A separate.
    Still using "amsu-b" only in geoips)

### Bug fixes
* **bdeck_parser.py**: Remove shell statement - raised error was dropping to shell during testing.
* **memusg.py** utility: Wrap import psutil in try/except so we don't fail if not installed
* **compare_outputs.py**: In test repo auto-generated update scripts, print gunzip before copy,
    and gzip after copy for files that must be gzipped before comparisons.
* **single_source and config_based**: Add newline to the end of "output_file_list", otherwise skipped during shell loop




# v1.4.4: 2022-03-06, command line override, unsectored product, product database support; Visible product corrections

### Test Repo Updates
* **Update ABI Visible Products with more informative colorbar label**
    * Include channel and wavelength in colorbar label
    * ABI static and TC Visible test png outputs

### Breaking Interface Changes
* **single_channel algorithm - rename solar zenith angle specifications**
    * See "Bug fixes"


### Improvements
* **Product tuning updates**
    * Add "update\_output\_dict\_from\_command\_line\_args" to support command line modifications to YAML output config
        * filename\_format\_kwargs
        * metadata\_filename\_format\_kwargs
    * Add "produce\_current\_time" function in output\_config interface
        * Support "produce\_times" field in output config to filter required times for processing
    * Add "Uncorrected-Channel" product, that just plots normalized data directly (using min/max of data itself)
    * Update colorbar labels for ABI, AHI, SEVIRI, MODIS, and VIIRS Visible imagery to include the channel used in the plot
    * dev/product.py get\_product: Loop through dictionary elements in product\_inputs, only replacing what exists.
        * To allow specifying only specific elements within one of the product parameters dictionaries
            from within product\_inputs specifications, if one of the dictionary elements is a dictionary
            itself, loop through that, replacing with the updated values found in product\_inputs.
        * This allows maintaining all the defaults, and only specifying things that must change.
    * Add "numpy\_arrays\_nan" coverage check interface module (for non-masked-arrays)
* **TC YAML Template Updates**
    * Add tc\_visir\_3200km YAML gridlines parameters file - identical to tc\_visir, but 5 degree grid spacing.
    * Created 1400x1400, 1024x1024, 256x256, 512x512, 800x800, and 1600x1600 subdirectories for tc templates.
        * 2km and 4km 1600x1600 TC template YAMLs
        * 4km 256x256
    * Will NOT change tc\_web\_template.yaml, etc, since ALL test scripts use those.
    * Perhaps explicitly setting these values in the YAML configs would be better than having
        completely separate files for each shape/resolution - will address direct YAML output
        config modifications at a later date - likely would be a method for overriding fields of
        TC template yamls, plotting\_params YAMLs, as well as product params YAMLs (so you could still use
        completely separate individual files, but also override individual fields within as needed).
* **Sectoring / Processing Order**
    * Add "resector=False" get\_alg\_xarray option to config\_based
        * this enables alg\_interp\_cmap and alg\_cmap product types (no pre-interpolation).
        * Currently "self\_register" and "reader\_defined" area\_def types lead to "resector=False" for get\_alg\_xarray.
            * Skip ALL sectoring for reader\_defined and self\_register.
    * Add xarray\_to\_numpy alg type support to get\_alg\_xarray
        * for alg\_interp\_cmap and alg\_cmap product types
            * no pre-interpolation - must pass sectored xarray, so can only include a single dataset
* **Product database support**
    * Added product database command line argument
    * Added hooks to single\_source and config\_based procflows
        * Checks if database environment variables are set
        * Uses yaml metadata file to populate the database
        * Prints "DATABASESUCCESS" for all products written to the database
* **Installation / Setup / Logging Process**
    * Separate vim8 installation and vim8 plugin setup in base\_install\_and\_test.sh
    * Remove verbose log statements including entire command line arguments
        * lots and lots of filenames, and now the command line call is printed on multiple lines separately

### Bug fixes
* **Resolve issues with Visible products**
    * Update AHI Visible parameters (was washed out / saturated)
        * gamma\_list: []
        * data\_range: [0.0, 120.0]
        * scalefactor still 100
    * Update MODIS Visible parameters (was all white)
        * gamma\_list: []
        * scale\_factor: 1.0 (comes out of the reader 0 to 100!)
    * Update Visible product
        * min\_day\_zen -> max\_day\_zen for single\_channel algorithm
        * Add comments that AHI and MODIS override standard parameters for Visible
    * SEVIRI reader reflectance calculations
        * reinstate: ref[rad > 0] = np.pi * rad[rad > 0] / irrad
            * Previously included solar zenith correction, so I had removed the entire line
        * Add log statements with min/max data values for reference
* **single_channel algorithm - rename solar zenith angle specifications**
    * rename min\_day\_zen -> max\_day\_zen
        * since day is 0-90, we want to identify the max zenith angle that will still be considered daytime
    * rename max\_night\_zen -> min\_night\_zen
        * night is 90-180, identify minimum zenith angle that will still be night
    * Updated Visible product with new names
* **Error Checking**
    * Added check in overpass\_predictor.py if sun.rise\_time exists
    * Added handling in amsub\_mirs reader for if there are bad ScanTime values


# v1.4.3: 2022-02-17, updated test scripts and documentation, jpss-1 to noaa-20

### Breaking Interface Changes
* **Replace jpss-1 with noaa-20 for VIIRS platform_name**
    * VIIRS reader
    * VIIRS Night Vis test outputs

### Major New Functionality
* **Minimum coverage capability**
    * Add minimum\_coverage option to command line arguments
    * Add minimum\_coverage / minimum\_coverages option to YAML output config
        * 'minimum\_coverage' covers all products
        * 'minimum\_coverages' dictionary is on a per-product basis
        * Special "all" key within minimum\_coverages dictionary applies to all products
            (can additionally specify individual products within dictionary).
    * Add get\_minimum\_coverage function to dev.output\_config interface module
* **Expanded example test scripts**
    * coverage over the various readers, products, and output formats
        * NEW Visible annotated ABI static
        * NEW IR-BD clean AHI TC
        * 89H-Physical annotated AMSR2 TC
        * 183-3H annotated AMSU-B TC
        * windbarbs clean ASCAT KNMI TC
        * Remove ASCAT UHR annotated windbarbs
        * NEW wind-ambiguities annotated ASCAT UHR TC
        * NEW 89pct clean GMI TC
        * windspeed annotated HY-2B TC
        * NEW Rain clean IMERG TC, no metadata
        * NEW TPW\_CIMSS MIMIC annotated global
        * NEW Infrared unprojected\_image MODIS
        * NEW windbarbs annotated OSCAT KNMI TC
        * NRCS annotated SAR TC
        * WV-Upper unprojected\_image SEVIRI
        * SMAP unsectored text winds (gzipped txt file)
        * SMOS sectored text winds (not gzipped txt file)
        * color89 unprojected\_image SSMIS (multiple granules, RGB)
        * REMOVE VIIRS IR-BD and Visible
        * Night-Vis-IR annotated VIIRS TC (day time! Need to update for night!)
    * Add documentation\_imagery.sh script to generate all imagery used in the available\_functionality.rst
        documentation, and copy it into the appropriate directory for use in documentation.
        Return non-zero if any of the commands failed (run\_procflow or copy)
    * Add minimum\_coverage and minimum\_coverages options to yaml\_configs/abi\_test.yaml for referencex
        (does not change output)
* **Expanded available functionality documentation**
    * Readers - each reader contains a global registered image for reference
        * ABI
        * AHI
        * EWS-G
        * SEVIRI
        * MODIS
        * SMAP (updated with full command)
        * SMOS (updated with full command)
        * HY2 (updted with full command and global registered image)
    * Output Formats
        * Unprojected Imagery
* **Additional test sectors**
    * bsh062022.dat b-deck file
    * bsh252020.dat b-deck file
    * bsh112022.dat b-deck file
    * bio022021.dat b-deck file
    * global.yaml 20km 1000x2000 global area\_def
* **Updated Night-Vis VIIRS products**
    * Added Night-Vis-GeoIPS1 and Night-Vis-IR-GeoIPS1 products for comparison with geoips versions

### Improvements
* Update imagery\_windbarbs to handle 1D vectors, 2-D vectors only, and 2-D vectors with ambiguitie
    (different numbers of arrays). Ambiguities were NOT getting plotted correctly previously.
* Update unprojected\_imagery to allow specifying either or both of x\_size and y\_size,
    and calculating the other if only one was included.
* Rename geoips test scripts to make it clear at a glance what reader, product, and output format they are testing.
* Print copy-and-pasteable command line call at the beginning of each run\_procflow call.
* Installation improvements
    * Separate base requirements from optional requirements.
    * Update setup\_geoips.sh install\_geoips to explicitly include all optional requirements.

### Bug fixes
* swap x\_size and y\_size for unprojected imagery
* Update EWS-G to "gvar" source name rather than gvissr
* Added uncompress test script to uncompress the .txt.gz unsectored text wind output.
* Update abi test script names in test\_base\_install.sh (no longer abi.sh and abi\_config.sh)
    * Call test\_base\_install.sh from test\_all.sh
    * Remove abi test calls from test\_all.sh, since they are included in test\_base\_install.sh


# v1.4.2: 2022-02-05, finalizing procflows to allow unprojected outputs, updating test outputs for consistent shapefiles

### Test Repo Updates
* Updated to Natural Earth Vector v5.0.0 shapefiles
    * AMSR2 TC image - very slightly modified political boundaries
    * AHI global image - very slightly modified political boundaries

### Major New Functionality
* SAR Incident Angle Product
    * Added "incident\_angle" variable to SAR xarray output
    * Added "incident-angle" product to "sar-spd" product\_inputs
    * Added "incident-angle" YAML product\_params, and test script
* ASCAT UHR windbarbs test script
* "unprojected\_image" output\_format module
    * Plots the data with no resampling - no area\_def required
    * Call signature: xarray\_obj, product\_name, output\_fnames, product\_name\_title=None, mpl\_colors\_info=None
                      x\_size=None, y\_size=None
* "unprojected" outputter\_type
    * Call signature: xarray\_obj, product\_name, output\_fnames, product\_name\_title=None, mpl\_colors\_info=None
* Support <DATASET>:<VARNAME> variable requests in product\_inputs YAML config files
    * Update VIIRS Night-Visible to use DNB:SunZenith
    * Update VIIRS Visible to use MOD:Sunzenith
    * Update AHI Visible to use MED:Sunzenith
* Added noaa-20 platform to amsub\_mirs reader
* Filter "poor" quality data within SMOS reader
    * previously was saving poor, fair, and good

### Improvements
* Installation Improvements
    * Allow skipping installation steps, rather than just continuing or quitting altogether
    * Separate steps for downloading cartopy map data and linking to ~/.local
    * Separate rclone, seviri, and vim8 installation steps (to allow skipping one or more if not needed)
* Updated command line arguments
    * sectored\_read / resampled\_read - specifications for primary dataset
        * Determines whether to read data initially or within area\_def loop
    * self\_register\_dataset, self\_register\_source, and self\_register\_platform
        * Explicitly request using specific dataset lat/lons as the area\_def target for resampling
        * Add self\_register area\_def specification in get\_area\_defs\_from\_commandline\_args
    * fuse\_sectored\_read / fuse\_resampled\_read - specifications for additional datasets
    * fuse\_self\_register\_dataset, fuse\_self\_register\_source, fuse\_self\_register\_platform
* Updated procflow ordering
    * Tunable data read order within procflows (based on data read requirements)
        * For self\_register or reader\_defined area\_defs - must read data prior to calling
             get\_area\_defs\_from\_commandline\_args (so area information is available within the xarray
            dataset when identifying area\_defs)
        * For externally specified area\_defs, read data after calling get\_area\_defs\_from\_commandline\_args,
            to reduce processing time if there is no coverage
        * For sectored\_read / resampled\_read data types, do not read data until we are within the area\_defs loop
    * Tunable algorithm order within procflows (based on alg\_type specified in dev/alg.py)
        * Support alg\_cmap and alg\_interp\_cmap algorithm types (previously only interp\_alg\_cmap supported -
            allow calling algorithm prior to data interpolation)
    * Tunable sectoring order within procflows (based on data read requirements)
        * Do not sector reader\_defined or self\_register sector types - must use full dataset, no padding available
    * Tunable outputter\_types within procflows (variable call signatures)
        * xarray\_data
        * image
        * image\_overlay
        * unprojected\_image
* Add mem\_usg and process\_times output to procflows for monitoring

### Bug fixes
* Update pmw\_37 and windbarbs algorithms to only include mandatory "arrays" argument, make output\_data\_range optional
    * If None, output\_data\_range will default to 230 to 280 for 37pct, and data min/max for windbarbs.
* Update single\_source procflow to ensure "resampled\_read" is passed to get\_alg\_xarray
    * to allow using the resampled dataset for retrieving the requested variables
    * if \<DATASET\_NAME>:\<VARIABLE\_NAME> construct used in product\_inputs YAML configs,
        we must assure resampled data is not limited to the native datasets,
        since they will no longer exist


# v1.4.1: 2022-01-21, viirs and smap output config test scripts and documentation

### Refactor
* Allow passing cbar\_ticks to matplotlib\_linear\_norm module

### Major New Functionality
* Add SMAP unsectored text winds explicit test call and sample output
* Add SMAP test script to test\_all.sh
* Add bwp202021.dat deck file with SMAP test dataset coverage
* Add VIIRS explicit test script and sample outputs
    * bsh192021.dat sector
    * IR-BD and Night-Vis-IR annotated imagery output
* Add himawari8 test sector
* Add VIIRS explicit est call to test\_all.sh

### Improvements
* Add aerosol reader and fname as arg options
* Add channel number as variable in AHI HSD reader
* Adjust selection of variable for interpolation in single\_source.py if the same variable name is contained in multiple datasets
 (ie, VIIRS geolocation variables - slightly different for each resolution dataset - caused issues with differing test outputs between single source and config\_based when multiple datasets are present)
    * Use variable from dataset that contains ALL required variables
    * Use variable from first dataset
* config\_based procflow now always sector to the adjusted area\_def to ensure we get all of the data.
    * Also must sector before adjusting the area\_def to ensure we have a consistent center time for determining new area\_def
      (slightly different center times resulting from different sectoring can cause very slightly different recentering)

### Documentation Updates
* Add VIIRS sensor and Night-Vis-IR product to avaialble functionality documentation
* Add SMAP unsectored text winds sample output to "available\_functionality" documentation

### Bug fixes
* Correct typo in config\_based.py (product\_name in pad\_alg\_xarrays, not alg\_xarrays)
* Update viirs\_netcdf.py to sort filenames prior to reading - intermittent failure if filenames are not sorted in advance
* No longer converting min/max value to int before normalizing in matplotlib\_linear\_norm colormap

# v1.4.0: 2022-01-10, add modular metadata output support, causing some internal interface changes

All interface changes due to this update are isolated to internal functions, required to support modular
metadata filename and output format specifications.  These changes will not impact any user/developer interfaces.

### Breaking Interface Changes
* Removed "overlay" procflow - functionality completely covered by config\_based procflow.
* remove\_duplicates:
    * Now takes dictionary of filenames with associated format information, rather than list of filenames
    * No longer takes separate "filename\_format" argument that must apply to all files
* single\_source.plot\_data
    * Takes in output\_dict rather than separate output file names and output format
    * Returns dictionary of output file names with associated filename formats, rather than list of filenames
    * Takes in variable for kwargs rather than \*\*kwargs
        (so it is explicit which kwargs should be applied to which module)
* single\_source.plot\_sectored\_data\_output (ie, sectored, unregistered outputs)
    * Takes in output\_dict rather than individual filename/output formats
    * Add area\_def argument
    * Returns dictionary of output file names with associated filename formats, rather than list of filenames
* single\_source.process\_xarray\_dict\_to\_output\_format (ie, unsectored, unregistered outputs)
    * Takes in output\_dict rather than individual filename/output formats
    * Add area\_def argument
    * Returns dictionary of output file names with associated filename formats, rather than list of filenames
* single\_source.get\_filename
    * (alg\_xarray, area\_def, filename\_format, product\_name)
        -> (filename\_format, product\_name=None, alg\_xarray=None, area\_def=None,
            output\_dict=None, suppored\_filenamer\_type=None)
    * Consolidated to support
        * metadata outputs
        * sectored/unsectored outputs
        * registered outputs
* Remove center coverage check from 89H-Physical product
    * For consistency with other products, request at the command line / output config level
    * Add center coverage product\_params\_override to direct command line amsr2.sh test call

### Refactor
* Pass "output\_dict" to all filename and output modules, for consistent application of options (allows
    specifying arguments via single\_source command line or output YAML config dict)
    * kwarg to all product modular interface functions
    * Optional kwarg to all filename and output modules (if it is not included as a kwarg, it is filtered
        out from within single\_source and not attempted to be passed in)
        * tc\_clean\_fname - for including coverage function information in filename
        * tc\_fname - for including coverage function information in filename
* single\_source.output\_all\_metadata
    * Returns dictionary of output filenames and formats
* single\_source.get\_output\_filenames
    * Returns dictionary of output\_filenames and metadata\_filenames with associated formats
* Separate test\_all.sh (includes test scripts that do not have bundled test data) and test\_base\_install.sh
    (only includes test scripts with bundled test data)
* Move "get\_bg\_xarray" from overlay procflow to config\_based procflow


### Major New Functionality
* Updated "product" modular interface
    * Add "list\_products\_by\_source" and "list\_products\_by\_products"
* Available functionality documentation page - includes readers and products, with examples
    * Readers
        * AMSU-B
        * HY2
        * SAR
        * SMOS
    * Products
        * 183-3H
        * NRCS
        * sectored text winds
        * unsectored text winds
* Sample test scripts with explicit command line call examples - input dataset NOT included, but
    all sector information and output comparison files are available directly within geoips
    * AMSR2 89H-Physical, using bdeck bio012020.dat
    * AMSU-B 183-3H, using bdeck bwp022021.dat
    * SAR windspeed, using bdeck bwp312018.dat
    * SMOS sectored, using bdeck bsh162020.dat
* Sectored and Unsectored text wind outputs
    * SAR
* Support user-defineable metadata output formats, command line args and YAML output config fields
    * metadata\_filename\_format (default None)
    * metadata\_filename\_format\_kwargs (default {})
    * metadata\_output\_format  (default None)
    * metadata\_output\_format\_kwargs (default {})
* Support user-defineable modifications to product parameters, via command line or output config fields
    * product\_params\_override (default {})
* Add "standard\_metadata" filename and output format types (to match version previously used automatically for
    all TC sectors - will continue to use "standard\_metadata" for testing purposes to avoid changing all
    test repo outputs)
* Add "output\_config" interface module to pull parameters from output config dictionaries
    * output\_config\_dict: full dictionary referring to complete YAML output config file
    * output\_dict: dictionary referring to a single set of output parameters for a single output type
        (subset of output\_config\_dict - matches "command\_line\_args" in single\_source procflow)

### Improvements
* Moved documentation imagery into subdirectories
    * available\_functionality
    * geoips\_overview
    * command\_line\_examples
* More informative log statement at the end of single\_source and config\_based procflows
* During output comparisons, name diff directory "diff\_test\_output\_dir" and files "diff\_test\_output"


# v1.3.2: 2021-12-21, title\_format interface

### Major New Functionality
    * Create dev/title.py interface for alternative title formats
        * Add interface_modules/title_formats
            * tc_standard.py (existing default)
            * static_standard.py (existing default)
            * tc_copyright.py (currently for hy2)
        * Pass "title_format" to annotated imagery and windbarbs
            * imagery_annotated.py
            * imagery_windbarbs.pycam

### Improvements
    * Updated template pull request ticket: Testing Instructions, Summary, Output, Individual Commits
    * Use dictionary of filename\_formats\_kwargs in YAML output configs rather than a single filename\_format\_kwarg
        * allows multiple filename_formats and specific kwargs for each
    * Allow passing "title\_copyright" from command line or YAML output config for use in annotated imagery
    * Added new DATABASESUCCESS and DATABASEFAILURE string checks to test\_all\_run.sh
    * Note disk space, memory, and time required at the beginning of geoips base installation
    * Use wget rather than curl for rclone setup for consistency
    * satpy>=0.33.1, pyresample>=1.22.3 for future geostationary geolocation improvements
    * Add "do\_not\_fail" option to repo update commands, to allow looping through all, and only updating those
        with the requested branch available (and not failing catastrophically on branches that don't exist)
    * Use a single consolidated "plot\_data" function for both single source and overlay functionality
        * Set up bg_xarray, bg_data, bg_mpl_colors_info, and bg_product_name_title kwargs within config_based procflow

### Bug fixes
    * Add rclone.conf file required for AWS ABI downloads
    * Correctly replace \*\_URL environment variables within geoips paths


# v1.3.1: 2021-12-07, hscat processing

### Refactor
    * Remove unused code
    * Use console scripts rather than calling command line python utilities explicitly
        * list_available_modules
        * test_interfaces

### Major New Functionality
    * Add hscat hy-2b and hy-2c processing
        * windspeed
        * windbarbs
        * unsectored text
        * sectored text
    * Add test script to test all dev and stable interfaces
        * list_available_modules
        * test_interfaces
    * imagery_windbarbs_clean output_format
    * output_format_kwargs and filename_format_kwargs options in YAML output config and command line
        * Useful for append, overwrite, basedir options
    * text_winds_day_fname with %Y%m%d dtg

### Bug fixes
    * Remove duplicates from list_<interface>s_by_type output
    * Update bdeck_parser to allow 30 or 38 or 40 or 42 fields
    * Include header in text wind output when the file does not exist, or we are not in append mode
    * Pass padded xarray to adjust_area_def for amsu-b data
        * amsu-b requires full swath width
    * Update to log filename for test scripts
        * command line arg now has ' ' and '/' replaced with '_' to get a single unique filename with no additional subdirectories

### Deprecations
    * Removed basemap-based windbarb plotting commands (no longer functional)


# v1.3.0: 2021-11-24, atcf->tc, update paths

### Breaking Interface Changes
    * Replaced instances of "atcf" within geoips repo with "tc"
        * --atcfdb command line option with --tcdb
        * --get_atcf_area_defs_for_xarray -> get_tc_area_defs_for_xarray
        * "atcf" -> "tc" sector_type
    * Removed support for deprecated environment variables / base_paths
        * GEOIPSFINAL -> ANNOTATED_IMAGERY_PATH
        * GEOIPSTEMP -> CLEAN_IMAGERY_PATH
        * PREGENERATED_IMAGERY_PATH -> CLEAN_IMAGERY_PATH
    * Update "geoips_outdirs" paths
        * geoips_outdirs/preprocessed/annotated_imagery
        * geoips_outdirs/preprocessed/clean_imagery
        * geoips_outdirs/longterm_files
    * Moved TCWWW, PUBLICWWW, and PRIVATEWWW directly under geoips_outdirs/preprocessed
        * Previously were under ANNOTATED_IMAGERY_PATH

### Breaking Test Repo Updates
    * Replaced sector_type "atcf" with "tc" in all TC metadata YAML outputs
    * Updated "geoips_outdirs" paths in metadata YAML outputs
        * geoips_outdirs/preprocessed/annotated_imagery
        * geoips_outdirs/preprocessed/clean_imagery
    * Updated TCWWW, PUBLICWWW, and PRIVATEWWW paths in metadata YAML outputs
        * preprocessed/annotated_imagery/tcwww -> preprocessed/tcwww
        * preprocessed/annotated_imagery/publicwww -> preprocessed/publicwww
        * preprocessed/annotated_imagery/privatewww -> preprocessed/privatewww

### Improvements
    * Simplified top level scripts
        * Moved Pull Request and Ticket Resolution templates into sphinx documentation
        * Moved entry point READMEs into sphinx documentation
    * Updated copy_diffs_for_eval.sh, delete_files_from_repo.sh, and delete_diff_dirs.sh to take "repo_name"
        * Previously ran on ALL repos.
        * Force user to select a specific repo to udpate
    * Updated tests README to include specific instructions for generating new test scripts
    * Added support for external compare_outputs module (to allow output type comparisons not specified within geoips)


# v1.2.5: 2021-11-18, bdeck parser, updated test scripts, test_interfaces.py, SMOS text winds

### Major New Functionality
    * bdeck parser in "trackfile_parsers"
    * SMOS 'unsectored' and 'sectored' text windspeed products
    * test_interfaces.py script to successfully test EVERY dev and stable interface module
        * Required non-breaking updates to attribute names and call signatures of some functionality modules

### Improvements
    * Only use ABI test scripts, since ABI test data can be obtained via rclone commands
        * Includes config-based and explicit call.
    * Add Software Requirements Specification to documentation
    * Update documentation with ABI test calls


# v1.2.4: 2021-11-12, original_source_filename->original_source_filenames, simplify setup

### Breaking Interface Changes
    * Replaced optional original_source_filename attribute with list of original_source_filenames

### Breaking Test Repo Updates
    * Replaced original_source_filename attribute with list of original_source_filenames
        * Updated all metadata YAML outputs
        * Updated all NetCDF outputs for datasets that had implemented the original_source_filename attribute
            in the reader

### Improvements
    * Automatically check command line args (including filenames) before attempting processing
    * Assume standard geoips_conda installation for standard config_geoips usage
        * Simplifies config files
        * Still allows individuals to override functionality and use their own environment
    * Simplified README installation steps
        * Create base_install_and_test.sh script that handles complete consistent conda-based geoips installation
        * remove "active_branch" (assume dev)


# v1.2.3: 2021-11-05, text wind outputs, internal dictionary of xarray datasets, unique TC filenames

### Breaking Interface Changes
    * Replaced internal lists of xarray datasets with dictionary of xarray datasets
        * xarray_utils/data.py sector_xarrays function now takes and returns dictionaries
        * procflows/single_source.py get_area_defs_from_command_line_args function now takes dictionary

### Breaking Test Repo Updates
    * Updated filenames to identify product implementation
        * bg<product_name> (ie, bgVisible) if background imagery was applied

### Major New Functionality
    * unsectored_xarray_dict_to_output_format product type
        * Hooks in single_source and config_based procflows to generate product immediately after reading data
    * sectored_xarray_dict_to_output_format product type
        * Hooks in single_source and config_based procflows to generate product immediately after sectoring
    * Text wind output capability
        * 'unsectored' and 'sectored' products
        * 'text_winds_full_fname' and 'text_winds_tc_fname' filename formats
    * SMAP and AMSR2 config-based processing

### Improvements
    * Updated test_all.sh script set up to take any script that has a valid exit code
        * Previously test scripts called from test_all.sh required specific setup
        * Updated to generically handle return codes from any scripts - simplifies testing setup
    * Updated test_all_run.sh sub-script to check log outputs for "success" strings before returning 0
        * If return is 0, grep the log output for one of a set of "success" strings
            * SETUPSUCCESS
            * FOUNDPRODUCT
            * SUCCESSFUL COMPARISON DIR
            * GOODCOMPARE
        * If no success strings are present, return 42.
        * protects against test scripts that inadvertently do not exit with the proper error code
    * Removed old testing construct - replace with explicit test scripts
        * config-based testing now handles the exhaustive functionality tests (much faster)
            * SMAP fully implemented
            * AMSR2 fully implemented
        * scripts with explicit command line call for minimal single_source and overlay functionality testing
    * Additional information in tc_fname extra field for different product enhancements
        * bg<product_name> (ie, bgVisible) if background imagery was applied
        * cr<radius> (ie, cr300) if center radius coverage check was used

### Bug fixes
    * Update all readers to include 'METADATA' field (now explicitly required)


# v1.2.2: 2021-10-25, config-based processing, global stitching, AWS-based test cases, separate sfc_winds readers

### Breaking Interface Changes
    * Separated all surface winds readers from sfc_winds_netcdf
        * smos_winds_netcdf
        * smap_remss_winds_netcdf
        * amsr2_remss_winds_netcdf
        * windsat_remss_winds_netcdf
        * scat_knmi_winds_netcdf
        * ascat_uhr_netcdf

### Breaking Test Repo Updates
    * Updated default padding amount from 2.5x to 1.5x
        * caused slightly modified output times in titles for some data types (identical data output, slightly modified center time)
            * test_data_ahi_day
            * test_data_amsr2
            * test_data_ascat_bin
            * test_data_smap
            * test_data_viirs

### Refactor
    * Separated all surface winds readers from sfc_winds_netcdf (see breaking interface changes)

### Major New Functionality:
    * Modular geostationary stitching capability
        * SEVIRI, ABI, and AHI
        * single channel products tested (Infrared-Gray and WV)

### Improvements
    * Single installation script with prompts to step through all installation/testing steps
        * Replaces step-by-step copy-paste in README with single call to full_nrl_installation.sh
    * Installation steps now return 1 for failed pulls and updates and fail catastrophically
        * Ensure timely notification of failure to reduce incomplete installations
        * Does not continue with further steps until all steps complete
    * Standard installation and testing now includes AWS-based ABI testing
        * Prevents requiring separate test data repo for basic testing -
            everything required is included in the geoips repo
            (comparison outputs, and commands to obtain test datasets).
    * Added SatZenith, sensor_scan_angle, and channel number attributes to PMW readers (supports CRTM)
        * SSMI/S
        * AMSU-B
        * AMSR2

### Bug fixes
    * Resolved issue with SMAP only processing one of the 2 daily overpasses
        * Previously always filtered dynamic area_defs to return a single area_def based on the data center_time
            * Now only return single area_def for data files covering < 3h
            * Now return ALL area_defs for data files covering > 3h
            * Now filter area_defs during processing - after sectoring datafile,
                check if the current area_def is the "closest", if not, skip.
    * Resolved bug in AMSU-b start and end time
        * Previously pulled start/end time from filename - test datafile actually had incorrect time listed!
        * Updated to pull directly from the metadata.


# v1.2.1: Test repo output updates (remove recentering, updated matplotlib/cartopy), and code refactor/simplification

### Breaking Interface Changes
    * remove_duplicates function now takes the explicit filename_format string, and returns the remove_duplicates
      method within the <filename_format> module.
    * Separated sar_netcdf reader from sfc_winds_netcdf.py
        * Eventually plan to separate all sfc_winds readers - they should all be independent modules.

### Breaking Test Repo Updates
    * Updated cartopy to 0.20.0 and matplotlib to v3.4.3
        * test repo outputs incompatible with matplotlib < 3.4.0 and cartopy < 0.19.0
        * Older versions have figures that are very slightly shifted from later versions
        * Exclusively a qualitative difference, but it *does* cause the test comparisons to fail
    * No longer recentering all TC outputs by default
        * General outputs are *not* recentered as of 1.2.1 - test recentering separately from other functionality

### Refactor
    * Moved metoctiff plugin to a separate installable repository
    * Moved recenter_tc plugin to a separate installable repository

### Major New Functionality:
    * Initial center radius coverage checks, for Tropical Cyclone applications
    * Initial SAR Normalized Radar Cross Section (NRCS) product implementation

### Improvements
    * Standardized and formalized the README, setup script, and test script format for all plugin repos
    * Removed requirement to link test scripts from plugin repos into the main geoips test directory

### Bug fixes
    * Added "METADATA" key in sfc_winds_netcdf.py return dictinoary


# v1.2.0: Major backwards incompatible update for stable and dev plugin interface implementation

### Breaking Interface Changes
    * Removed all deprecated code
    * Developed dev interface for accessing modules, moved plugins to geoips/interface_modules
        * algorithms, area_def_generators, coverage_checks, filename_formats, interpolation,
          mtif_params, output_formats, procflows, trackfile_parsers, user_colormaps
    * Developed finalized stable interface, moved stable plugins to geoips/interface_modules
        * readers
    * Consolidated YAML config files in geoips/yaml_configs

### Refactor
    * Moved geoips package into subdirectory for pip installability

### Major New Functionality:
    * Exhaustive test scripts with final return value of 0 for successful completion of all functionality
    * dev and stable interfaces, allowing entry point based plugins
    * Initial geotiff output support
    * Initial full disk output support
    * Night Visible products
    * Gdeck and flat sectorfile trackfile parsers

### Improvements
    * YAML based product specifications (references colormaps, algorithms,
      interpolation routines, coverage checks, etc)

### Bug fixes
    * Resolved sectoring issue, allowing complete center coverage
        * Previously when sectoring based on min/max lat/lon, any values outside the explicit
          requested values would be masked, causing masked data on non-square datasets when
          good data was actually available for the entire requested region. Only drop rows outside
          requested range, do not mask data.

### Performance Upgrades
    * Initial config-based processing implementation, which will allow efficiently processing
      multiple output types in a single run.



# v1.1.17: Rearranged for stable interface implementation

### Removed Code
    * drivers/autotest_*
        * Previously automated test scripts relied on specific autotest drivers for each sensor. Update
          to allow for generalized drivers, and shell scripts that drive for specific sensors.

# v1.1.16: rearranged for pip installability for open source release, product updates per JTWC request

### Refactor:
    * Moved fortran algorithms into separate repositories
    * Identified differences between 1.1.3 and 1.1.16
        * Restored and marked retired code as deprecated

### Major New Functionality:
    * Created sector overpass database
    * Turned on Visible global stitched
    * Allow ASCAT ESA primary solutions text output
    * Implemented API structure for accessing modules from multiple repos
        (unused, but functional)

### Improvements:
    * Updated 89H and 89H-Legacy color schemes per JTWC request
    * Switched active MTIFs from smoothed new colormaps to nearest neighbor "legacy" colormaps
    * Apply color ranges to PMW products directly rather than relying on matplotlibs normalize routine.

### Bug fixes:
    * Partially resolved RGB MTIF color issue (0 is bad val)
    * Corrected TC web output (was matching dictionary keys incorrectly)
    * Resolved multiple errors with MODIS global stitched processing.


# v1.1.15 Change Log

### Refactor:
    * BREAKING CHANGE: Modularized PMW algorithms and colormaps
    * Finalized bash setup to enable Python 3 exclusive operation

### Improvements:
    * Update 37H and 89H colormaps to more closely match Legacy colormaps,
        but with extended range
    * Standardize Visible products

### Features:
    * MODIS reader
    * Finalized stitched product output


# v1.1.14 Change Log

### Refactor:
    * BREAKING CHANGE: "channels" dictionary in algorithms now contains lists of
                    variables by default (rather than a single variable)

### Features:
    * Overpass predictor database - polar orbiting and geostationary satellites
    * Upper and lower level water vapor algorithms, MODIS Visible algorithm
    * Add FINAL_DATA_PATH variable in base_paths for default final processed data output location
    * Allow output netcdf filenames using subset of field names
    * Generalized product stitching capability for single channel products
    * Initial attempt at parallax correction in generalized stitched products
    * Allow text trackfile based processing

### Fix:
    * Resolve errors when XRIT decompress software is missing


# v1.1.3 -> v1.1.13 Change Log


### (Pending) Remove Code:

    * old_tcweb_fnames (Added tc_lon argument to old_tcweb_fnames)
    * Remove products/pmw_mint.py


### (Pending) Deprecation Warnings

    * find_modules_in_geoips_packages -> find_modules
        *Corrected find module terminology and added support for different module and method names
        * PREVIOUS find_modules_in_geoips_packages(module_name, method_name)
            * from geoips.module_name.method_name import method_name  # Always same method name
        * UPDATED find_modules_in_geoips_packages(subpackage_name, module_name, method_name=None)
            * from geoips.subpackage_name.module_name import method_name
        * Imports in "drivers" will require updating to new terminology. Note this will all go away with Tim entry points

    * geoips_modules / $GEOIPS_MODULES_DIR -> geoips_packages and $GEOIPS_PACKAGES_DIR
        * These are convenience variables / directory structures for storing multiple geoips repositories.
        * Updated modules to packages for accurate naming conventions, handle discrepancies in gpaths/config
        * Note this will also all go away with Tim entry points


### Breaking Changes

    * BREAKING CHANGE: standardized platform names
        * sen1 -> sentinel-1, metopa -> metop-a, metopb -> metop-b, metopc -> metop-c, radarsat2 -> radarsat-2
        * NOAA-19 -> noaa-19, NOAA-18 -> noaa-18, amsub -> amsu-b,

    * BREAKING CHANGE: Changed wind_speed to vmax in sector_info dictionary for TCs ALSO CHANGED IN PYROCB!!!!!!!
        * Change track_type -> aid_type

    * BREAKING CHANGE: Renamed area_def -> area_definition xarray attribute


### Deprecation Warnings

    * get_area_defs_for_xarray -> get_static_area_defs_for_xarray AND get_atcf_area_defs_for_xarray
        * (added get_trackfile_area_defs)

    * commandline run_yaml_from_deckfile.py -> convert_trackfile_to_yaml.py

    * commandline update_atcf_database.py -> update_tc_tracks_database.py

    * sector_utils/atcf_tracks.py -> sector_utils/tc_tracks.py
        * sector_utils/atcf_database.py -> tc_tracks_database.py

    * colormaps.py -> colormap_utils.py - moved colormaps into subpackage user_colormaps

    * moved set_matplotlib_colors_standard from mpl_utils to colormap_utils
        * -    from geoips.image_utils.mpl_utils import set_matplotlib_colors_standard
        * +    from geoips.image_utils.colormap_utils import set_matplotlib_colors_standard

    * products/global_stitched -> products/stitched

    * some imports from mpl_utils moved to user_colormaps and/or colormap_utils
        * -from geoips.image_utils.mpl_utils import set_matplotlib_colors_37H
        * +from geoips.image_utils.user_colormaps.pmw import set_matplotlib_colors_37H
        * +from geoips.image_utils.colormap_utils import set_matplotlib_colors_standard
        * +from geoips.image_utils.user_colormaps.winds import set_matplotlib_colors_winds


### Refactoring

    * Created separate modules for each visir and pmw products within algorithms/visir and algorithms/pmw
        * Previously all separate products were combined within products/visir.py and products/pmw_tb.py

    * Standardized geolocation generation for ABI/AHI/SEVIRI


### New Readers

    * Added amsu-b MIRS reader

    * Added MIMIC reader

    * Added MODIS hdf4 reader


### Performance Upgrades

    * For xarray sectoring - pass "check_center" and "drop" to allow checking coverage based on the center of the image,
        and completely dropping rows and columns that are unneeded


### New functionality

    * Added additional command line arguments:
        * atcf_db, atcf_db_sectorlist to specify TC processing based on the TC database
        * trackfiles, trackfile_parser, and trackfile_sectorlist to specify processing based on the flat sectorfile
    * Added support for arbitrary TC trackfile parsing - currently flat sectorfile and G-decks
    *  Added xml_to_yaml geoips1 sectorfile conversion utility
    *  Added parallax_correction argument to data_manipulations.merge.merge_data
        * Currently does not blend msg-1 with AHI near the equator, later could implement optical flow based corrections
    *  Allow building documentation for alternative geoips packages, not only geoips
    *  Added ambiguity wind barb plotting
    *  Added global stitched imagery capability
    *  Added TPW processing
    *  Allow optional fields for netcdf output filename
    *  Fully support xml -> yaml conversions for geoips1 sectorfiles.
    *  Replace '-' with '_' in method and module names for find_modules
    *  Added overpass predictor
    *  Added static sector database
    *  Added database of TC overpasses


### Bug Fixes

    * Resolved bug with transparency behind titles / borders for cartopy plotting
    * Ensure metadata goes in _dev directory if product is in _dev directory
    * Use make_dirs for netcdf write (sets permissions) rather than os.makedirs()
