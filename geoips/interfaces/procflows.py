from geoips.interfaces.base import BaseInterface, BasePlugin


class ProcflowsInterface(BaseInterface):
    name = "procflows"
    deprecated_family_attr = "procflow_type"


procflows = ProcflowsInterface()


# class ProcflowsPlugin(BasePlugin):
#     interface = procflows
