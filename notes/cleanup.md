## Deprecations not currently used
We currently aren't using deprecations anywhere in the code but various methods
of raising a deprecation warning are defined in a few locations. We should cut
this down to one or zero.

Current declarations:
- dev.utils.deprecation
- geoips_utils.deprecation (imports from geoips.dev.utils)
- utils/decorators.deprecated


## dev/utils.py
Anything that we want to keep from here is going to need to move. We will be
getting rid of the `dev` directory. Current functions include:
- deprecation
  - Move this to geoips_utils.py I think
  - Imported in geoips_utils.py
  - Unsure if used elsewhere
- replace_geoips_paths
  - Move this to geoips_utils.py for now but may want to figure out if it is
    actually needed in the long-run
  - metadata_default.py
  - metadata_tc.py
  - bdeck_parser.py
  - tc_tracks.py
- copy_standard_metadata
  - Move this to geoips_utils.py
    - Update imports in interp_nearest, interp_grid, interp_gauss,
      netcdf_geoips, and single_source
  - Imported in geoips_utils.py
  - Unsure if used elsewhere
- get_required_geoips_xarray_attrs
  - Move to geoips_utils.py
  - Used in compare_outputs.py
- output_process_times
  - Move to geoips_utils.py
    - Update imports in data_fusion.py, config_based.py, single_source.py, and the
      ahi_hsd
  - Imported in geoips_utils.py
  - Unsure if used elsewhere

## Additional interfaces
Should the following have actual interfaces? They are accessed via entry points which
seems to imply that they should be interfaces.
- recenter_tc: area_def_adjusters
- geoips: sector_adjusters (same as area_def_adjusters?)
- geoips: output_comparisons