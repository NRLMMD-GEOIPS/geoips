from typing import Literal, Tuple, Union, Optional

from pydantic import Field, BaseModel, confloat, conint, root_validator, field_validator

from geoips.pydantic.bases import Plugin, LatLonCoordinate


class XYCoordinate(BaseModel):
    x: float
    y: float


class SectorProjection(BaseModel, extra="allow"):
    """Projection information for a sector as required by the AreaDefinition class."""

    # This sets "a" to be a constant value of 6371228.0
    # I honetly don't know where this comes from, but it's been used for all of the
    # sectors we have. I'm not sure if it's a good idea to hardcode this value.
    a: Literal[6371228.0] = 6371228.0
    lat_0: confloat(ge=-90, le=90)
    lon_0: confloat(ge=-180, le=180)
    proj: str
    units: Literal["m", "km"]


class SectorShape(BaseModel, extra="forbid"):
    """The shape of the sector in pixels."""

    height: conint(gt=0)
    width: conint(gt=0)


class SectorResolution(BaseModel, extra="forbid"):
    """The resolution of the sector in projection units.

    The height and width of pixels in the units specified by the sector's projection
    units.
    """

    height: conint(gt=0)
    width: conint(gt=0)


class SectorAreaExtent(BaseModel):
    lower_left_xy: Tuple[int, int]
    upper_right_xy: Tuple[int, int]


class AreaDefinitionSpec(BaseModel):
    """Defines an AreaDefinition for use with pyresample.

    The resulting dictionary should be able to just be passed to
    ``pyresample.create_area_def()``.
    """

    area_id: str = None
    description: str = None
    projection: SectorProjection = None
    # This can either be a tuple of integers (preferred) or a
    # SectorShape object (deprecated)
    shape: Union[Tuple[conint(gt=0), conint(gt=0)], SectorShape] = None
    area_extent: Union[Tuple[float, float, float, float], SectorAreaExtent] = None
    resolution: Union[
        confloat(gt=0), Tuple[confloat(gt=0), confloat(gt=0)], SectorShape
    ] = None
    center: Union[Tuple[float, float], XYCoordinate] = (0, 0)

    # @root_validator(pre=True)
    # def set_area_id_and_description(cls, values):
    #     """If area_id is not provided, use the name from the parent Sector."""
    #     print("Using parent values")
    #     from IPython import embed as shell

    #     shell()
    #     parent = values.get("_parent")
    #     if parent and not values.get("area_id"):
    #         values["area_id"] = parent.name
    #     if parent and not values.get("description"):
    #         values["description"] = parent.docstring
    #     return values


class CenterSpec(BaseModel):
    projection: str
    center: LatLonCoordinate


class StaticMetadata(BaseModel):
    pass


class PyrocbMetadata(BaseModel):
    pass


class AtmosRiverMetadata(BaseModel):
    pass


class StitchedRiverMetadata(BaseModel):
    pass


class TCMetadata(BaseModel):
    pass


class VolcanoMetadata(BaseModel):
    pass


class Sector(Plugin):
    spec: Union[AreaDefinitionSpec, CenterSpec]
    metadata: Union[
        StaticMetadata,
        PyrocbMetadata,
        AtmosRiverMetadata,
        StitchedRiverMetadata,
        TCMetadata,
        VolcanoMetadata,
    ]

    @field_validator("spec", mode="before")
    @classmethod
    def add_parent(cls, value, info):
        if "area_id" not in value or not value["area_id"]:
            value["area_id"] = info.data["name"]
        if "description" not in value or not value["description"]:
            value["description"] = info.data["docstring"]
        return value
