from geoips.interfaces.base import BaseInterface, BasePlugin


class ProcflowsInterface(BaseInterface):
    name = "procflows"
    deprecated_family_attr = "procflow_type"
    required_args = {"standard": ["fnames"]}
    required_kwargs = {"standard": ["command_line_args"]}


procflows = ProcflowsInterface()
