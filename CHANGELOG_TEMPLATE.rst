.. dropdown:: Distribution Statement

 | # # # This source code is protected under the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

The GeoIPS Ecosystem uses ``brassy`` for automating RST release note generation from
user-generated YAML release notes.  Every pull request within the GeoIPS GitHub
organization must have valid YAML release notes in the ``docs/source/releases/latest/``
directory prior to being approved and merged.

1. Run `brassy -t docs/source/releases/latest/<branch_name>.yaml` to create a template
   release note that you can modify.
2. Edit brassy YAML release note template with all updates made on current branch.

   * Select appropriate category as found in the template, or create your own!

     * Empty sections in the YAML template can remain - they will be ignored.
   * **Title** should be a short description of the change, < 120 characters, preferably <60
   * **Description** can be multiple lines (use proper YAML formatting), with additional
     details.
   * Always include a list of add/modified/deleted **files** for each entry.
   * **Related Issue** ID should match related linked issue, like: NRLMMD-GEOIPS/geoips#27
