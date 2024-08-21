# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Driver configs interface module."""

from types import SimpleNamespace

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

    def __init__(self, obj_attrs):
        """Initialize the DriverConfigs plugin object, then assign new attributes.

        Where each attribute assigned to 'self' is each key found in the class' 'spec'
        object contained in its yaml file.

        Will include by default:
            - basedir
            - output_types
            - products
            - sector_mapping
            - paths
        Extra defaults are allowed.

        Parameters
        ----------
        obj_attrs: dict
            - A dictionary of attributes to assign to the class.
        """
        # Initialize the class using 'BaseYamlPlugin'
        super().__init__(obj_attrs)
        # Now assign each key of 'spec' as an attribute to this class. See
        # schema.yaml.driver_configs.specs.default for more information.
        for key in self["spec"]:
            setattr(self, key, self["spec"][key])


class DriverConfigsInterface(BaseYamlInterface):
    """Configuration values that are used to drive GeoIPS for NRT processing."""

    name = "driver_configs"
    plugin_class = DriverConfigsPlugin


driver_configs = DriverConfigsInterface()
