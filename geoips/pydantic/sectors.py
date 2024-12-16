# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.


from typing import Literal, Tuple, Union, Optional

from pydantic import (
    Field,
    BaseModel,
    ConfigDict,
    confloat,
    conint,
    field_validator,
)

from geoips.pydantic.bases import PluginModel, LatLonCoordinate


class XYCoordinate(BaseModel):
    """A coordinate in projection units."""

    x: float = Field(None, description="The x coordinate in projection units.")
    y: float = Field(None, description="The y coordinate in projection units.")


class SectorProjection(BaseModel, extra="allow"):
    """Projection information for a sector.

    This is a dictionary that provides Proj projection information for the sector. For
    more information on what parameters can be supplied, see the Proj documentation.

    Validation has only been implemented for some of the most common options. If you
    need validation for a parameter that is not currently implemented, please open an
    issue and, if possible, a pull request on GitHub.
    """

    # This sets "a" to be a constant value of 6371228.0
    # I honetly don't know where this comes from, but it's been used for all of the
    # sectors we have. I'm not sure if it's a good idea to hardcode this value.
    proj: str = Field(description="Proj projection alias.")
    a: Literal[6371228.0] = Field(
        6371228.0, description="Semimajor axis of the ellipsoid in meters."
    )
    lat_0: confloat(ge=-90, le=90) = Field(
        None, description="Latitude of origin in degrees."
    )
    lon_0: confloat(ge=-180, le=180) = Field(
        None, description="Longitude of origin in degrees."
    )
    units: Literal["m", "km"] = Field(
        "m",
        description=(
            "Units of the projection. "
            "This should not need to be changed from the default. "
            "This controls the units of the x and y coordinates in the projection but "
            "has no impact on the units of the resolution or area_extent because we "
            "specify those units separately."
        ),
    )


class SectorShape(BaseModel, extra="forbid"):
    """The shape of the sector in pixels."""

    height: conint(gt=0) = Field(
        None,
        description="The height of the sector in pixels. Must be greater than 0.",
    )
    width: conint(gt=0) = Field(
        None,
        description="The width of the sector in pixels. Must be greater than 0.",
    )


class SectorResolution(BaseModel, extra="forbid"):
    """The resolution of the sector in projection units.

    The height and width of pixels in the units specified by the sector's projection
    units.
    """

    dx: confloat(gt=0) = Field(
        description=(
            "The width of pixels in the units specified by "
            "the sector's projection units."
        )
    )
    dy: confloat(gt=0) = Field(
        description=(
            "The height of pixels in the units specified by "
            "the sector's projection units."
        )
    )


class SectorAreaExtent(BaseModel):
    """The extent of the sector in projection units.

    For more information on how this is used, see the pyresample documentation.
    """

    lower_left_xy: Tuple[int, int] = Field(
        None,
        description="Lower left corner of the sector in projection units.",
    )
    upper_right_xy: Tuple[int, int] = Field(
        None,
        description="Upper right corner of the sector in projection units. ",
    )


class AreaDefinitionSpec(BaseModel):
    """Defines an AreaDefinition for use with pyresample.

    The resulting dictionary should be able to just be passed to
    ``pyresample.create_area_def()``.
    """

    area_id: str = Field(
        None,
        description=(
            "A name for the resulting pyresample AreaDefinition. "
            "Defaults to the sector's name."
        ),
    )
    description: str = Field(
        None,
        description=(
            "A description for the resulting pyresample AreaDefinition. "
            "Defaults to the sector's docstring."
        ),
    )
    projection: SectorProjection = Field(
        description=(
            "A dictionary providing Proj projection information for the sector. "
            "For more information please see the Proj documentation."
        ),
    )
    # This can either be a tuple of integers (preferred) or a
    # SectorShape object (deprecated)
    shape: Union[Tuple[conint(gt=0), conint(gt=0)], SectorShape] = None
    area_extent: Union[Tuple[float, float, float, float], SectorAreaExtent] = Field(
        None,
        description=(
            "Sector area extent in projection units. "
            "For more information see the pyresample documentation."
        ),
    )
    resolution: Union[
        confloat(gt=0), Tuple[confloat(gt=0), confloat(gt=0)], SectorResolution
    ] = Field(
        None,
        description=(
            "The size of the pixels in the sector in projection units. "
            "May be specified as a single float or a tuple of two floats "
            "describing the resolution in the x and y directions separately."
            "See the pyresample documentation for more information."
        ),
    )
    units: Literal["m", "km", "meters", "kilometers", "deg", "degrees"] = Field(
        "m",
        description=(
            "The units used for resolution and area_extent. "
            "This takes priority over the units specified in the projection. "
            "For more information on this parameter and its priority order, see the "
            "pyresmaple documentation."
        ),
    )

    center: Union[Tuple[float, float], XYCoordinate] = Field(
        (0, 0),
        description=(
            "The center of the sector in projection units. Defaults to (0, 0). "
            "See the pyresample documentation for more information."
        ),
    )


class CenterSpec(BaseModel):
    """Placeholder comment."""

    projection: str
    center: LatLonCoordinate
    shape: Union[Tuple[int, int], SectorShape]
    resolution: Union[float, Tuple[float, float], SectorResolution]


class StaticMetadata(BaseModel):
    """Metadata format for standard static sectors."""

    continent: str = None
    country: str = None
    area: str = None
    subarea: str = None
    state: str = None
    city: str = None


class BoxMetadata(BaseModel):
    """Metadata format for pyroCb sectors."""

    min_lat: confloat(ge=-90, le=90)
    min_lon: confloat(ge=-180, le=180)
    max_lat: confloat(ge=-90, le=90)
    max_lon: confloat(ge=-180, le=180)
    box_resolution_km: confloat(gt=0)


class StitchedMetadata(StaticMetadata):
    """Metadata for stitched imagery sectors."""

    primary_area_definition: str


class TCMetadata(BaseModel):
    """Metdata format for Tropical Cyclone sectors."""

    pressure: confloat(gt=0)
    vmax: confloat(gt=0)
    clat: confloat(ge=-90, le=90)
    clon: confloat(ge=-180, le=180)
    # synoptic_time: datetime
    aid_type: str
    storm_num: conint(gt=0)
    storm_name: str
    storm_basin: str
    storm_year: conint(gt=1900)
    deck_line: str
    source_file: str
    final_storm_name: str


class VolcanoMetadata(BaseModel):
    """Metadata format for Volcano sectors."""

    summit_elevation: float = Field(description="Elevation of the volcano's summit.")
    plume_height: float = Field(description="Altitude of the volcanic plume.")
    wind_speed: confloat(gt=0)
    wind_dir: confloat(ge=0, le=360)
    clat: confloat(ge=-90, le=90)
    clon: confloat(ge=-180, le=180)


class Sector(PluginModel):
    """Sector PluginModel format."""

    spec: Union[AreaDefinitionSpec, CenterSpec] = Field(
        description=(
            "Specification of the sector's geographical domain. "
            "Used to generate a pyresample AreaDefinition."
        ),
    )
    metadata: Union[
        BoxMetadata,
        StaticMetadata,
        StitchedMetadata,
        TCMetadata,
        VolcanoMetadata,
    ] = Field(
        description=(
            "Metadata describing the sector "
            "(mostly used in FilenameFormatters and MetadataFormatters)."
        )
    )

    @field_validator("spec", mode="before")
    @classmethod
    def add_parent(cls, value, info):
        """Collect default area_id and description from parent.

        This is a field validator that runs before the root validator. It accesses the
        properties of the parent object to fill in area_id and description if they are
        not provided. These values come from the parent's name and docstring.
        """
        if "area_id" not in value or not value["area_id"]:
            value["area_id"] = info.data["name"]
        if "description" not in value or not value["description"]:
            value["description"] = info.data["docstring"]
        return value
