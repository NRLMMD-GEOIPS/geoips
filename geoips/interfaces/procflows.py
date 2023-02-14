from geoips.interfaces.base import BaseInterface, BasePlugin


class ProcflowsInterface(BaseInterface):
    """Class-based interface for processing workflows (procflows).

    Proclows drive a specific collection of steps for a particular type of
    processing.  Currently available are:
    
    * single_source: single input type and single output type.
    * overlay: two input types (one for foreground and one for background),
      with a single output type.
    * config_based: efficient method for producing all possible outputs for a
      given set of data files.
    """

    name = "procflows"
    deprecated_family_attr = "procflow_type"


procflows = ProcflowsInterface()

