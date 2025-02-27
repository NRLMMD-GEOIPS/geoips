"""Pydantic models used to validate GeoIPS sector plugins."""

from datetime import datetime
from enum import Enum
from typing import Literal, Tuple, Union
from typing_extensions import Annotated

from pydantic import (
    Field,
    BaseModel,
    ConfigDict,
    field_validator,
)
from pydantic.functional_validators import AfterValidator

from geoips.pydantic.bases import PluginModel


class EarthConstants(float, Enum):
    """A simple class containing constant values relative to the geometry of Earth."""

    SEMI_MAJOR_AXIS = 6371228.0  # Semimajor axis of the earth in meters.


class XYCoordinate(BaseModel):
    """A coordinate in projection units."""

    x: float = Field(None, description="The x coordinate in projection units.")
    y: float = Field(None, description="The y coordinate in projection units.")


def lat_lon_coordinate(arg: tuple[float, float]) -> tuple[float, float]:
    """Validate a latitude and longitude coordinate."""
    if arg[0] < -90 or arg[0] > 90:
        raise ValueError("Latitude must be between -90 and 90")
    if arg[1] < -180 or arg[1] > 180:
        raise ValueError("Longitude must be between -180 and 180")
    return arg


LatLonCoordinate = Annotated[Tuple[float, float], AfterValidator(lat_lon_coordinate)]


# Ex: Change inheritance to PermissiveFrozenModel
class SectorProjection(BaseModel, extra="allow"):
    """Projection information for a sector.

    This is a dictionary that provides Proj projection information for the sector. For
    more information on what parameters can be supplied, see the Proj documentation.

    Validation has only been implemented for some of the most common options. If you
    need validation for a parameter that is not currently implemented, please open an
    issue and, if possible, a pull request on GitHub.
    """

    proj: str = Field(..., description="Proj projection alias.")
    a: EarthConstants = Field(
        EarthConstants.SEMI_MAJOR_AXIS,
        description="Semimajor axis of the ellipsoid in meters.",
    )
    R: Annotated[
        float,
        Field(
            None,
            strict=True,
            ge=0,
            description=(
                "Radius of the sphere, given in meters. If used in conjunction with "
                "``+ellps``, :option:`+R` takes precedence."
                "See https://proj.org/en/stable/usage/ellipsoids.html#ellipsoid-size-parameters "  # NOQA
                "for more information."
            ),
        ),
    ]
    ellps: str = Field(
        "GRS80",
        description=(
            "The name of a built-in ellipsoid definition. "
            "See https://proj.org/en/stable/usage/ellipsoids.html#built-in-ellipsoid-definitions "  # NOQA
            " for more information, or execute :option:`proj -le` for a list of "
            "built-in ellipsoid names."
            "*Defaults to 'GRS80'.*"
        ),
    )
    h: Annotated[
        float,
        Field(
            None,
            strict=True,
            ge=0,
            description=(
                "Height of the view point above the Earth and must be in the same units"
                " as the radius of the sphere or semimajor axis of the ellipsoid."
            ),
        ),
    ]
    k_0: Annotated[
        float,
        Field(
            1.0,
            strict=True,
            ge=0,
            description=(
                "Scale factor. Determines scale factor used in the projection."
                "*Defaults to 1.0.*"
            ),
        ),
    ]
    lat_0: Annotated[
        float,
        Field(
            None,
            strict=True,
            ge=-90,
            le=90,
            description="Latitude of origin in degrees.",
        ),
    ]
    lat_1: Annotated[
        float,
        Field(
            0.0,
            strict=True,
            ge=-90,
            le=90,
            description=("First standard parallel." "*Defaults to 0.0.*"),
        ),
    ]
    lat_2: Annotated[
        float,
        Field(
            0.0,
            strict=True,
            ge=-90,
            le=90,
            description=("Second standard parallel." "*Defaults to 0.0.*"),
        ),
    ]
    lat_ts: Annotated[
        float,
        Field(
            0.0,
            strict=True,
            ge=0,
            description=(
                "Latitude of true scale. Defines the latitude where scale is not "
                "distorted."
                "Takes precedence over ``+k_0`` if both options are used together."
                "*Defaults to 0.0.*"
            ),
        ),
    ]
    lon_0: Annotated[
        float,
        Field(
            None,
            strict=True,
            ge=-180,
            le=180,
            description="Longitude of origin in degrees.",
        ),
    ]
    t_epoch: float = Field(None, description=("Central epoch of the transformation."))
    t_final: float = Field(
        None,
        description=(
            "Final epoch that the coordinate will be propagated to after transformation."  # NOQA
            "The special epoch *now* can be used instead of writing a specific period in"  # NOQA
            "time. When *now* is used, it is replaced internally with the epoch of the "
            "transformation. This means that the resulting coordinate will be slightly "
            "different if carried out again at a later date."
        ),
    )
    x_0: float = Field(
        0.0,
        description=(
            "False easting, easting at false origin or easting at projection centre "
            "(naming and meaning depend on the projection method). Always in meters."
            "*Defaults to 0.0.*"
        ),
    )
    y_0: float = Field(
        0.0,
        description=(
            "False northing, northing at false origin or northing at projection centre "
            "(naming and meaning depend on the projection method). Always in meters."
            "*Defaults to 0.0.*"
        ),
    )
    units: Literal["m", "km", "degrees"] = Field(
        "m",
        description=(
            "Units of the projection. "
            "This should not need to be changed from the default. "
            "This controls the units of the x and y coordinates in the projection but "
            "has no impact on the units of the resolution or area_extent because we "
            "specify those units separately."
        ),
    )


# Ex: Change inheritance to FrozenModel
class SectorShape(BaseModel, extra="forbid"):
    """The shape of the sector in pixels."""

    height: Annotated[
        int,
        Field(
            ...,
            strict=True,
            gt=0,
            description="The height of the sector in pixels. Must be greater than 0.",
        ),
    ]
    width: Annotated[
        int,
        Field(
            ...,
            strict=True,
            gt=0,
            description="The width of the sector in pixels. Must be greater than 0.",
        ),
    ]


class SectorResolution(BaseModel, extra="forbid"):
    """The resolution of the sector in projection units.

    The height and width of pixels in the units specified by the sector's projection
    units.
    """

    dx: Annotated[
        float,
        Field(
            ...,
            strict=True,
            gt=0,
            description=(
                "The width of pixels in the units specified by "
                "the sector's projection units."
            ),
        ),
    ]
    dy: Annotated[
        float,
        Field(
            ...,
            strict=True,
            gt=0,
            description=(
                "The height of pixels in the units specified by "
                "the sector's projection units."
            ),
        ),
    ]


class SectorAreaExtent(BaseModel):
    """The extent of the sector in projection units.

    For more information on how this is used, see the pyresample documentation.
    """

    lower_left_xy: Tuple[int, int] = Field(
        ...,
        description="Lower left corner of the sector in projection units.",
    )
    upper_right_xy: Tuple[int, int] = Field(
        ...,
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
        ...,
        description=(
            "A dictionary providing Proj projection information for the sector. "
            "For more information please see the Proj documentation."
        ),
    )
    # This can either be a tuple of integers (preferred) or a
    # SectorShape object (deprecated)
    shape: Union[
        Tuple[
            Annotated[int, Field(strict=True, gt=0)],
            Annotated[int, Field(strict=True, gt=0)],
        ],
        SectorShape,
    ] = None
    area_extent: Union[Tuple[float, float, float, float], SectorAreaExtent] = Field(
        None,
        description=(
            "Sector area extent in projection units. "
            "For more information see the pyresample documentation."
        ),
    )
    resolution: Union[
        Annotated[float, Field(strict=True, gt=0)],
        Tuple[
            Annotated[float, Field(strict=True, gt=0)],
            Annotated[float, Field(strict=True, gt=0)],
        ],
        SectorResolution,
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
    """Model for how to specify the center of a sector plugin."""

    projection: str = Field(..., description="Name of the PROJ projection in use.")
    center: LatLonCoordinate = Field(
        ..., description="Lat/Lon center coordinate in degrees."
    )
    shape: Union[Tuple[int, int], SectorShape] = Field(
        ..., description="Shape of the sector in pixels."
    )
    resolution: Union[float, Tuple[float, float], SectorResolution] = Field(
        ..., description="Resolution of the sector in projection units."
    )


class RegionMetadata(BaseModel):
    """Metadata format for standard static sectors covering a specific region."""

    model_config = ConfigDict(coerce_numbers_to_str=False, extra="forbid")

    continent: str = Field(..., description="Continent which the sector resides in.")
    country: str = Field(..., description="Country which the sector resides in.")
    area: str = Field(..., description="Geographic area of the sector.")
    subarea: str = Field(..., description="Geographic subarea of the sector.")
    state: str = Field(..., description="State which the sector resides in.")
    city: str = Field(..., description="City which the sector resides in.")


class StaticMetadata(BaseModel):
    """Metadata format for standard static sectors."""

    region: RegionMetadata = Field(
        ...,
        description=(
            "Metadata format for standard static sectors covering a specific region."
        ),
    )


class BoxMetadata(BaseModel):
    """Metadata format for pyroCb sectors."""

    min_lat: Annotated[
        float,
        Field(
            ...,
            strict=True,
            ge=-90,
            le=90,
            description="Bottom left latitude in degrees.",
        ),
    ]
    min_lon: Annotated[
        float,
        Field(
            ...,
            strict=True,
            ge=-180,
            le=180,
            description="Bottom left longitude in degrees.",
        ),
    ]
    max_lat: Annotated[
        float,
        Field(
            ...,
            strict=True,
            ge=-90,
            le=90,
            description="Upper right latitude in degrees.",
        ),
    ]
    max_lon: Annotated[
        float,
        Field(
            ...,
            strict=True,
            ge=-180,
            le=180,
            description="Upper right longitude in degrees.",
        ),
    ]

    box_resolution_km: Annotated[
        float,
        Field(
            ...,
            strict=True,
            gt=0,
            description="The resolution of each pixel in kilometers.",
        ),
    ]


class StitchedMetadata(StaticMetadata):
    """Metadata for stitched imagery sectors."""

    primary_area_definition: str = Field(
        ..., description="Name of the area definition to be used."
    )


class TCMetadata(BaseModel):
    """Metdata format for Tropical Cyclone sectors."""

    pressure: Annotated[
        float,
        Field(
            ..., strict=True, gt=0, description="Pressure of the storm in millibars."
        ),
    ]
    vmax: Annotated[
        float,
        Field(
            ...,
            strict=True,
            gt=0,
            description="Maximum velocity in knots of the storm.",
        ),
    ]
    clat: Annotated[
        float,
        Field(
            ..., strict=True, ge=-90, le=90, description="Center latitude of the storm."
        ),
    ]
    clon: Annotated[
        float,
        Field(
            ...,
            strict=True,
            ge=-180,
            le=180,
            description="Center longitude of the storm.",
        ),
    ]
    synoptic_time: datetime = Field(..., description="Synoptic time of the storm.")
    aid_type: str = Field(..., description="Tropical cyclone forecast aid category.")
    storm_num: Annotated[
        int,
        Field(
            ...,
            strict=True,
            gt=0,
            description=(
                "Two digit storm number in sequential order from the start of the "
                "hurricane season."
            ),
        ),
    ]
    storm_name: str = Field(description="Name of the storm.")
    storm_basin: str = Field(
        ...,
        description=(
            "Two character representation of the basin in which the storm originated "
            "in."
        ),
    )
    storm_year: Annotated[
        int,
        Field(
            ...,
            strict=True,
            gt=1900,
            description="Year in which the storm originated, after 1900.",
        ),
    ]
    deck_line: str = Field(
        ...,
        description=(
            "Deck data file used within the weather forecasting system for this storm."
        ),
    )
    source_file: str = Field(..., description="File in which the storm data came from.")
    final_storm_name: str = Field(
        ...,
        description="Final name of the storm used within the track file.",
    )


class VolcanoMetadata(BaseModel):
    """Metadata format for Volcano sectors."""

    summit_elevation: float = Field(
        ..., description="Elevation of the volcano's summit."
    )
    plume_height: float = Field(..., description="Altitude of the volcanic plume.")
    wind_speed: Annotated[
        float,
        Field(..., strict=True, gt=0, description="Windspeed of the volcano sector."),
    ]
    wind_dir: Annotated[
        float,
        Field(
            ...,
            strict=True,
            ge=0,
            le=360,
            description="Angular direction of wind within the volcano sector.",
        ),
    ]
    clat: Annotated[
        float,
        Field(
            ...,
            strict=True,
            ge=-90,
            le=90,
            description="Center latitude of the volcano sector.",
        ),
    ]
    clon: Annotated[
        float,
        Field(
            ...,
            strict=True,
            ge=-180,
            le=180,
            description="Center longitude of the volcano sector.",
        ),
    ]


class SectorPluginModel(PluginModel):
    """Sector plugin format."""

    model_config = ConfigDict(extra="allow")
    spec: Union[AreaDefinitionSpec, CenterSpec] = Field(
        ...,
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
        ...,
        description=(
            "Metadata describing the sector "
            "(mostly used in FilenameFormatters and MetadataFormatters)."
        ),
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
