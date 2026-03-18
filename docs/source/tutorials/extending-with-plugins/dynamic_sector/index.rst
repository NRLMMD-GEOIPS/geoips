.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _create-a-dynamic_sector:

Extend GeoIPS with a new Dynamic Sector
***************************************


Dynamic Sectors are a geolocated sectors in GeoIPS that contain data that is dynamic
in time and/or space. Common cases include tropical cyclones, volcanoes, atmospheric
rivers, wildfires, or dust storms. Several components of GeoIPS help create the dynamic 
sectoring capabilities, mainly, the dynamic sector yaml file, track file, track
file parser, and the dynamic area definition file. 

In this example, we will walk through the steps needed to create and implement
a dynamic sector for the 2022 Tonga Volcano explosion. Current files, code, and 
test data is within GeoIPS already.

Creating a Dynamic Sector
-------------------------

We will create a small dynamic sector to help capture the initial plume 
from the volcanic explosion. The docstring should contain useful 
information for yourself or other users.

.. code-block:: yaml

    interface: sectors
    family: generated
    name: volc_tonga
    docstring: |
        Volcano dynamic sector for Tonga.
        Shape: 1400 x 1400 pixels
        Resolution: 1km x 1km
    spec:
      sector_spec_generator:
        name: center_coordinates
        arguments:
          projection: eqc
          pixel_width: 1000
          pixel_height: 1000
          num_lines: 1400
          num_samples: 1400


Each component under the spec arguments is similar to the static sector 
arguments. Projection is the desired projection of the dynamic sector, defined
in PROJ keywords, pixel width and height are the resolution of the dynamic sector,
and num lines and samples are tied to the shape of the output dynamic sector.

This dyanmic sector works in conjuction with the trackfile and 
parser to create a dynamic area with the size, and resolution specified 
by the yaml file.

Creating a Trackfile 
--------------------

Trackfiles within GeoIPS help users specify the dynamic components of the feature of 
interest, whether it be tied to a bulletin like output, or an output csv. The core
components of a trackfile should be the latitude, longitude, and time, additional 
components could be storm name, scale factor (for dynamic sized sectors), or metadata.
Trackfile should be easily created from bulletins, notices, or dynamic alerts, that in
turn get parsed by the trackfile parser.

A sample trackfile for the tonga volcano could look like:

.. code-block:: bash

    Lat,Lon,Time,Name
    -20.545,-175.3925,20220115T0330,TONGA
    -20.545,-175.3925,20220115T0340,TONGA
    -20.545,-175.3925,20220115T0350,TONGA


For a more complex example or use case, users should reference the tropical cyclone 
trackfiles (bdeck_files).

Creating a Trackfile Parser
---------------------------

Trackfile parsers translate a trackfile content to a list of dictionary values, which
in turn gets transformed to a dynamic area definition. Required information parsed
from the trackfile is latitude, longitude, and time, however users can include 
additional information if needed. 

To parse the trackfile above, we would create the following code:

.. code-block:: python 

    import pandas as pd

    LOG = logging.getLogger(__name__)

    interface = "sector_metadata_generators"
    family = "volc"
    name = "volc_parser"

    
    def call(trackfile_name):
        """Parse a sample volcano csv file.

        Parameters
        ----------
        trackfile_name: str, or path
            * Path to trackfile csv file with the format:
            * columns: lat lon time
            * lat/lon format: decimal
            * time format: YYYYMMDDTHHMM
        """
        csv_parser = pd.read_csv(trackfile_name)

        all_fields = []
        for i in csv_parser.iterrows():
            # grab the row number
            tmp_fields = i[1]
            fields = {}
            # grab the lat and lon field
            fields["clat"] = tmp_fields["Lat"]
            fields["clon"] = tmp_fields["Lon"]
            # parse time to a datetime.datetime obj
            fields["time"] = pd.to_datetime(tmp_fields["Time"]).to_pydatetime()
            # append it all as a dict
            all_fields.append(fields)

        volcano_name = tmp_fields["Name"]
        if "volcano" not in volcano_name.lower():
            # append volcano so its the volcano not just geographic location
            volcano_name = volcano_name.upper() + "_VOLCANO"
        # grab the year and set aid type to BEST
        # could change AID type if we get different bulletin sources
        return all_fields, volcano_name, fields["time"].strftime("%Y"), "BEST"


The parser works in tandem with the trackfile, users should have a specific 
trackfile format, and in turn, a specific trackfile parser. A majority of dynamic 
features are novel, so the resulting components of it should also be unique.

Creating a Dynamic Area Function
--------------------------------

After parsing the trackfile, the resulting output gets mapped to sector_utils
where a pyresample AreaDefinition object is created from the trackfile 
parsed data. Users should add hooks into sector_utils.tc_tracks to indicate 
when the specified parser should be used, one method could be checking the 
final_storm_name variable.

Note: This functionality and feature might be refactored in the future to 
be easier to implement and use.

Using Your Dynamic Sector
-------------------------

Each component can now be accessed from the CLI and tested with some data.

.. code-block:: bash 

    geoips run single_source \
        ${GEOIPS_TESTDATA_DIR}/test_data_volc/data/ahi/20220115/* \
        --reader_name ahi_hsd \
        --product_name Infrared \
        --filename_formatter geoips_fname \
        --output_formatter imagery_annotated \
        --trackfile_parser volc_parser \
        --trackfiles $GEOIPS/tests/sectors/volc_csv/tonga_trackfile.csv \
        --tc_spec_template volc_tonga



Output
------

With everything intergrated, the output should look like below.
