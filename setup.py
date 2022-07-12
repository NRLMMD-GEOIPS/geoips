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

'''Installation instructions for base geoips package'''

from os.path import realpath, join, dirname

import setuptools

with open(join(dirname(realpath(__file__)), 'VERSION'), encoding='utf-8') as version_file:
    version = version_file.read().strip()

setuptools.setup(
    name='geoips',
    version=version,
    packages=setuptools.find_packages(),
    install_requires=['pyresample',           # Base requirement - efficiency improvements >= 1.22.3
                      'numpy',                # Base requirement
                      'xarray',               # Base requirement
                      'matplotlib',           # Base requirement
                      'scipy',                # Base requirement
                      'netcdf4',              # Base requirement
                      'pyyaml',               # Base requirement
                      # 'cartopy==0.20.2',    # Currently must install via conda
                      ],
    extras_require={
                    'config_based': [
                                     'pyaml_env',          # Reading YAML output config files, with paths
                                     ],
                    'hdf5_readers': [
                                     'h5py',               # hdf5 readers (GMI)
                                     ],
                    'hdf4_readers': [
                                     'pyhdf',              # hdf4 readers (MODIS)
                                     ],
                    'geotiff_output': [
                                       'rasterio',           # GEOTIFF output
                                       ],
                    'syntax_checking': [
                                        'flake8',             # Syntax checking
                                        'pylint',             # Syntax checking
                                        'bandit',             # Syntax/security checking
                                        ],
                    'documentation': [
                                      'sphinx',             # Required for building documentation
                                      ],
                    'debug': [
                              'ipython',            # Required for Debugging purposes
                              'psutil',             # Required for memory checks
                              ],
                    'overpass_predictor': [
                                           'pyorbital',          # required by satpy
                                           'ephem',              # Required for overpass predictor
                                           'isodate',            # Required for overpass predictor
                                           ],
                    'geostationary_readers': [
                                              'satpy',      # efficiency improvements >= 0.33.1
                                              'numexpr',            # for efficiency improvements
                                              ],
                    'test_outputs': [
                                     'pyshp>=2.2.0',       # Previously 2.1.3, 20220607 3.5.2
                                     'matplotlib>=3.5.2',  # Previously v3.3, then 3.4.3, 20220607 3.5.2
                                     ],
                    'efficiency_improvements': [
                                     'satpy>=0.36.0',      # efficiency improvements >= 0.33.1, 20220607 0.36.0
                                     'pyresample>=1.23.0',   # efficiency improvements >= 1.22.3, 20220607 1.23.0
                                     ],
                    },
    entry_points={
        'console_scripts': [
            'run_procflow=geoips.commandline.run_procflow:main',
            'convert_trackfile_to_yaml=geoips.commandline.convert_trackfile_to_yaml:main',
            'update_tc_tracks_database=geoips.commandline.update_tc_tracks_database:main',
            'xml_to_yaml_sector=geoips.commandline.xml_to_yaml_sector:main',
            'test_interfaces=geoips.commandline.test_interfaces:main',
            'list_available_modules=geoips.commandline.list_available_modules:main',
        ],
        'geoips.readers': [
            'abi_netcdf=geoips.interface_modules.readers.abi_netcdf:abi_netcdf',
            'abi_l2_netcdf=geoips.interface_modules.readers.abi_l2_netcdf:abi_l2_netcdf',
            'ahi_hsd=geoips.interface_modules.readers.ahi_hsd:ahi_hsd',
            'amsr2_netcdf=geoips.interface_modules.readers.amsr2_netcdf:amsr2_netcdf',
            'amsr2_remss_winds_netcdf=geoips.interface_modules.readers.amsr2_remss_winds_netcdf'
            ':amsr2_remss_winds_netcdf',
            'amsub_hdf=geoips.interface_modules.readers.amsub_hdf:amsub_hdf',
            'amsub_mirs=geoips.interface_modules.readers.amsub_mirs:amsub_mirs',
            'atms_hdf5=geoips.interface_modules.readers.atms_hdf5:atms_hdf5',
            'ewsg_netcdf=geoips.interface_modules.readers.ewsg_netcdf:ewsg_netcdf',
            'geoips_netcdf=geoips.interface_modules.readers.geoips_netcdf:geoips_netcdf',
            'gmi_hdf5=geoips.interface_modules.readers.gmi_hdf5:gmi_hdf5',
            'imerg_hdf5=geoips.interface_modules.readers.imerg_hdf5:imerg_hdf5',
            'mimic_netcdf=geoips.interface_modules.readers.mimic_netcdf:mimic_netcdf',
            'modis_hdf4=geoips.interface_modules.readers.modis_hdf4:modis_hdf4',
            'saphir_hdf5=geoips.interface_modules.readers.saphir_hdf5:saphir_hdf5',
            'seviri_hrit=geoips.interface_modules.readers.seviri_hrit:seviri_hrit',
            'ascat_uhr_netcdf=geoips.interface_modules.readers.ascat_uhr_netcdf:ascat_uhr_netcdf',
            'smap_remss_winds_netcdf=geoips.interface_modules.readers.smap_remss_winds_netcdf:smap_remss_winds_netcdf',
            'smos_winds_netcdf=geoips.interface_modules.readers.smos_winds_netcdf:smos_winds_netcdf',
            'scat_knmi_winds_netcdf=geoips.interface_modules.readers.scat_knmi_winds_netcdf:scat_knmi_winds_netcdf',
            'windsat_remss_winds_netcdf=geoips.interface_modules.readers.windsat_remss_winds_netcdf'
            ':windsat_remss_winds_netcdf',
            'sar_winds_netcdf=geoips.interface_modules.readers.sar_winds_netcdf:sar_winds_netcdf',
            'sfc_winds_text=geoips.interface_modules.readers.sfc_winds_text:sfc_winds_text',
            'ssmi_binary=geoips.interface_modules.readers.ssmi_binary:ssmi_binary',
            'ssmis_binary=geoips.interface_modules.readers.ssmis_binary:ssmis_binary',
            'viirs_netcdf=geoips.interface_modules.readers.viirs_netcdf:viirs_netcdf',
            'wfabba_ascii=geoips.interface_modules.readers.wfabba_ascii:wfabba_ascii',
            'windsat_idr37_binary=geoips.interface_modules.readers.windsat_idr37_binary:windsat_idr37_binary',
        ],
        'geoips.output_formats': [
            'full_disk_image=geoips.interface_modules.output_formats.full_disk_image:full_disk_image',
            'unprojected_image=geoips.interface_modules.output_formats.unprojected_image:unprojected_image',
            'geotiff_standard=geoips.interface_modules.output_formats.geotiff_standard:geotiff_standard',
            'imagery_annotated=geoips.interface_modules.output_formats.imagery_annotated:imagery_annotated',
            'imagery_clean=geoips.interface_modules.output_formats.imagery_clean:imagery_clean',
            'imagery_windbarbs=geoips.interface_modules.output_formats.imagery_windbarbs:imagery_windbarbs',
            'imagery_windbarbs_clean=geoips.interface_modules.output_formats.imagery_windbarbs_clean'
            ':imagery_windbarbs_clean',
            'netcdf_geoips=geoips.interface_modules.output_formats.netcdf_geoips:netcdf_geoips',
            'netcdf_xarray=geoips.interface_modules.output_formats.netcdf_xarray:netcdf_xarray',
            'text_winds=geoips.interface_modules.output_formats.text_winds:text_winds',
            'metadata_default=geoips.interface_modules.output_formats'
            '.metadata_default:metadata_default',
            'metadata_tc=geoips.interface_modules.output_formats'
            '.metadata_tc:metadata_tc',
        ],
        'geoips.algorithms': [
            'single_channel=geoips.interface_modules.algorithms.single_channel:single_channel',
            'pmw_tb.pmw_37pct=geoips.interface_modules.algorithms.pmw_tb.pmw_37pct:pmw_37pct',
            'pmw_tb.pmw_89pct=geoips.interface_modules.algorithms.pmw_tb.pmw_89pct:pmw_89pct',
            'pmw_tb.pmw_color37=geoips.interface_modules.algorithms.pmw_tb.pmw_color37:pmw_color37',
            'pmw_tb.pmw_color89=geoips.interface_modules.algorithms.pmw_tb.pmw_color89:pmw_color89',
            'sfc_winds.windbarbs=geoips.interface_modules.algorithms.sfc_winds.windbarbs:windbarbs',
            'visir.Night_Vis_IR=geoips.interface_modules.algorithms.visir.Night_Vis_IR:Night_Vis_IR',
            'visir.Night_Vis_IR_GeoIPS1=geoips.interface_modules.algorithms'
            '.visir.Night_Vis_IR_GeoIPS1:Night_Vis_IR_GeoIPS1',
            'visir.Night_Vis_GeoIPS1=geoips.interface_modules.algorithms.visir.Night_Vis_GeoIPS1:Night_Vis_GeoIPS1',
            'visir.Night_Vis=geoips.interface_modules.algorithms.visir.Night_Vis:Night_Vis',
        ],
        'geoips.procflows': [
            'single_source=geoips.interface_modules.procflows.single_source:single_source',
            'config_based=geoips.interface_modules.procflows.config_based:config_based',
        ],
        'geoips.trackfile_parsers': [
            'flat_sectorfile_parser=geoips.interface_modules.trackfile_parsers.flat_sectorfile_parser'
            ':flat_sectorfile_parser',
            'bdeck_parser=geoips.interface_modules.trackfile_parsers.bdeck_parser:bdeck_parser',
        ],
        'geoips.area_def_generators': [
            'clat_clon_resolution_shape=geoips.interface_modules.area_def_generators.clat_clon_resolution_shape'
            ':clat_clon_resolution_shape',
        ],
        'geoips.interpolation': [
            'pyresample_wrappers.interp_nearest=geoips.interface_modules.interpolation.pyresample_wrappers'
            '.interp_nearest:interp_nearest',
            'pyresample_wrappers.interp_gauss=geoips.interface_modules.interpolation.pyresample_wrappers'
            '.interp_gauss:interp_gauss',
            'scipy_wrappers.interp_grid=geoips.interface_modules.interpolation.scipy_wrappers.interp_grid:interp_grid',
        ],
        'geoips.user_colormaps': [
            'cmap_rgb=geoips.interface_modules.user_colormaps.cmap_rgb:cmap_rgb',
            'matplotlib_linear_norm=geoips.interface_modules.user_colormaps.matplotlib_linear_norm'
            ':matplotlib_linear_norm',
            'pmw_tb.cmap_150H=geoips.interface_modules.user_colormaps.pmw_tb.cmap_150H:cmap_150H',
            'pmw_tb.cmap_37H_Legacy=geoips.interface_modules.user_colormaps.pmw_tb.cmap_37H_Legacy:cmap_37H_Legacy',
            'pmw_tb.cmap_37H_Physical=geoips.interface_modules.user_colormaps.pmw_tb.cmap_37H_Physical'
            ':cmap_37H_Physical',
            'pmw_tb.cmap_37H=geoips.interface_modules.user_colormaps.pmw_tb.cmap_37H:cmap_37H',
            'pmw_tb.cmap_37pct=geoips.interface_modules.user_colormaps.pmw_tb.cmap_37pct:cmap_37pct',
            'pmw_tb.cmap_89H_Legacy=geoips.interface_modules.user_colormaps.pmw_tb.cmap_89H_Legacy'
            ':cmap_89H_Legacy',
            'pmw_tb.cmap_89H_Physical=geoips.interface_modules.user_colormaps.pmw_tb.cmap_89H_Physical'
            ':cmap_89H_Physical',
            'pmw_tb.cmap_89H=geoips.interface_modules.user_colormaps.pmw_tb.cmap_89H:cmap_89H',
            'pmw_tb.cmap_89pct=geoips.interface_modules.user_colormaps.pmw_tb.cmap_89pct:cmap_89pct',
            'pmw_tb.cmap_89HW=geoips.interface_modules.user_colormaps.pmw_tb.cmap_89HW:cmap_89HW',
            'pmw_tb.cmap_Rain=geoips.interface_modules.user_colormaps.pmw_tb.cmap_Rain:cmap_Rain',
            'tpw.tpw_cimss=geoips.interface_modules.user_colormaps.tpw.tpw_cimss:tpw_cimss',
            'tpw.tpw_purple=geoips.interface_modules.user_colormaps.tpw.tpw_purple:tpw_purple',
            'tpw.tpw_pwat=geoips.interface_modules.user_colormaps.tpw.tpw_pwat:tpw_pwat',
            'visir.Infrared=geoips.interface_modules.user_colormaps.visir.Infrared:Infrared',
            'visir.IR_BD=geoips.interface_modules.user_colormaps.visir.IR_BD:IR_BD',
            'visir.WV=geoips.interface_modules.user_colormaps.visir.WV:WV',
            'winds.wind_radii_transitions=geoips.interface_modules.user_colormaps.winds.wind_radii_transitions'
            ':wind_radii_transitions',
        ],
        'geoips.filename_formats': [
            'geoips_fname=geoips.interface_modules.filename_formats.geoips_fname:geoips_fname',
            'geoips_netcdf_fname=geoips.interface_modules.filename_formats.geoips_netcdf_fname:geoips_netcdf_fname',
            'geotiff_fname=geoips.interface_modules.filename_formats.geotiff_fname:geotiff_fname',
            'tc_fname=geoips.interface_modules.filename_formats.tc_fname:tc_fname',
            'tc_clean_fname=geoips.interface_modules.filename_formats.tc_clean_fname:tc_clean_fname',
            'text_winds_day_fname=geoips.interface_modules.filename_formats.text_winds_day_fname'
            ':text_winds_day_fname',
            'text_winds_full_fname=geoips.interface_modules.filename_formats.text_winds_full_fname'
            ':text_winds_full_fname',
            'text_winds_tc_fname=geoips.interface_modules.filename_formats.text_winds_tc_fname:text_winds_tc_fname',
            'metadata_default_fname=geoips.interface_modules.filename_formats'
            '.metadata_default_fname:metadata_default_fname',
        ],
        'geoips.title_formats': [
            'tc_standard=geoips.interface_modules.title_formats.tc_standard:tc_standard',
            'tc_copyright=geoips.interface_modules.title_formats.tc_copyright:tc_copyright',
            'static_standard=geoips.interface_modules.title_formats.static_standard:static_standard',
        ],
        'geoips.coverage_checks': [
            'masked_arrays=geoips.interface_modules.coverage_checks.masked_arrays:masked_arrays',
            'numpy_arrays_nan=geoips.interface_modules.coverage_checks.numpy_arrays_nan:numpy_arrays_nan',
            'center_radius=geoips.interface_modules.coverage_checks.center_radius:center_radius',
            'center_radius_rgba=geoips.interface_modules.coverage_checks.center_radius_rgba:center_radius_rgba',
            'rgba=geoips.interface_modules.coverage_checks.rgba:rgba',
            'windbarbs=geoips.interface_modules.coverage_checks.windbarbs:windbarbs',
        ],
        'geoips.output_comparisons': [
            'compare_outputs=geoips.compare_outputs:compare_outputs',
        ],
    }
)
