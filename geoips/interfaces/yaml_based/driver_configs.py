# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Driver configs interface module."""

from geoips.interfaces.base import BaseYamlInterface, BaseYamlPlugin


class DriverConfigsPlugin(BaseYamlPlugin):
    """Class for yaml-based configuration plugins which support driving GeoIPS.

    Exposes top-level information and adds a few methods that make accessing
    configuration information easier that parsing through the yaml's spec.

    A driver will create output in this order:

    For each output_type:
        For each product:
            # If implemented in your driver
                For each sector:
                    produce an output
            # Else (for a singular sector)
                produce an output
    """

    @property
    def basedir(self):
        """Base directory where your files could arrive to."""
        if not hasattr(self, "_basedir"):
            self._basedir = self["spec"]["basedir"]
        return self._basedir

    @property
    def output_types(self):
        """List of output types GeoIPS will create with your driver."""
        if not hasattr(self, "_output_types"):
            self._output_types = self["spec"]["output_types"]
        return self._output_types

    @property
    def products(self):
        """List of products GeoIPS will create with your driver."""
        if not hasattr(self, "_products"):
            self._products = self["spec"]["products"]
        return self._products

    @property
    def sector_mapping(self):
        """Dictionary of 'satellite_sector_name': 'geoips_sector_name'.

        Maps sectors that may appear in the arriving data file paths to a geoips sector.
        """
        if not hasattr(self, "_sector_mapping"):
            self._sector_mapping = self["spec"]["sector_mapping"]
        return self._sector_mapping

    @property
    def paths(self):
        """Dictionary of relative file paths based on sat, sensor, sector.

        An entry for CLAVR-x GOES16 data could look like:
        'GOES16':
          'ABI':
            'RadC': <some_path>
            'RadF': <some_path>
        """
        if not hasattr(self, "_paths"):
            self._paths = self["spec"]["paths"]
        return self._paths


class DriverConfigsInterface(BaseYamlInterface):
    """Configuration values that are used to drive GeoIPS for NRT processing."""

    name = "driver_configs"
    plugin_class = DriverConfigsPlugin


driver_configs = DriverConfigsInterface()
