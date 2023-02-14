from geoips.interfaces.base import BaseInterface, BasePlugin


class OutputFormatsInterface(BaseInterface):
    name = "output_formats"
    deprecated_family_attr = "output_type"
    required_args = {'image': ['area_def',
                               'xarray_obj',
                               'product_name',
                               'output_fnames'
                               ],
                     'unprojected': ['xarray_obj', 'product_name', 'output_fnames'],
                     'image_overlay': ['area_def',
                                       'xarray_obj',
                                       'product_name',
                                       'output_fnames'
                                       ],
                     'image_multi': ['area_def',
                                     'xarray_obj',
                                     'product_names',
                                     'output_fnames',
                                     'mpl_colors_info'
                                     ],
                     'xrdict_area_varlist_to_outlist': ['xarray_dict',
                                                        'area_def',
                                                        'varlist'
                                                        ],
                     'xrdict_area_product_outfnames_to_outlist': ['xarray_dict',
                                                                  'area_def',
                                                                  'product_name',
                                                                  'output_fnames'
                                                                  ],
                     'xrdict_varlist_outfnames_to_outlist': ['xarray_dict',
                                                             'varlist',
                                                             'output_fnames'
                                                             ],
                     'xarray_data': ['xarray_obj', 'product_names', 'output_fnames'],
                     'standard_metadata': ['area_def',
                                           'xarray_obj',
                                           'metadata_yaml_filename',
                                           'product_filename'
                                           ],
                     }

output_formats = OutputFormatsInterface()

