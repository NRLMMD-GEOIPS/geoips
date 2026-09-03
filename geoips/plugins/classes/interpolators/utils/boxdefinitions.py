# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Classes for geometry operations allowing masked data in swath corners.

This package uses the pyresample geometry package as base classes:

# pyresample, Resampling of remote sensing image data in python
#
# Copyright (C) 2010-2015
#
# Authors:
#    Esben S. Nielsen
#    Thomas Lavergne
"""

from __future__ import absolute_import

# Python Standard Libraries
import warnings
import math
import logging

# Installed Libraries
import numpy as np
from pyproj import Geod
from pyresample import utils
from pyresample.geometry import SwathDefinition, CoordinateDefinition

log = logging.getLogger(__name__)

interface = None

EPSILON = 0.0000001


class MaskedCornersSwathDefinition(SwathDefinition):
    """Swath defined by lons and lats.

    Allows datasets with potentially masked data in the corners.

    Parameters
    ----------
    lons : numpy array
        Longitude values
    lats : numpy array
        Latitude values
    nprocs : int, optional
        Number of processor cores to be used for calculations.

    Attributes
    ----------
    shape : tuple
        Swath shape
    size : int
        Number of elements in swath
    ndims : int
        Swath dimensions

    Properties
    ----------
    lons : object
        Swath lons
    lats : object
        Swath lats
    cartesian_coords : object
        Swath cartesian coordinates
    """

    def __init__(self, lons, lats, nprocs=1):
        """Initialize class."""
        if lons.shape != lats.shape:
            raise ValueError("lon and lat arrays must have same shape")
        elif lons.ndim > 2:
            raise ValueError("Only 1 and 2 dimensional swaths are allowed")

        if lons.shape == lats.shape and lons.dtype == lats.dtype:
            self.shape = lons.shape
            self.size = lons.size
            self.ndim = lons.ndim
            self.dtype = lons.dtype
        else:
            raise ValueError(
                (
                    "%s must be created with either "
                    "lon/lats of the same shape with same dtype"
                )
                % self.__class__.__name__
            )

        lats_type = type(lats)
        lons_type = type(lons)

        if lats_type != lons_type:
            raise TypeError("lons and lats must be of same type")
        elif lons is not None:
            if lons.shape != lats.shape:
                raise ValueError("lons and lats must have same shape")

        self.nprocs = nprocs

        # check the latitutes
        if lats is not None and ((lats.min() < -90.0 or lats.max() > +90.0)):
            # throw exception
            raise ValueError("Some latitudes are outside the [-90.;+90] validity range")
        else:
            self.lats = lats

        # check the longitudes
        if lons is not None and ((lons.min() < -180.0 or lons.max() >= +180.0)):
            # issue warning
            warnings.warn(
                "All geometry objects expect longitudes in the [-180:+180[ range. "
                "We will now automatically wrap your longitudes into [-180:+180[, "
                "and continue. "
                "To avoid this warning next time, use routine utils.wrap_longitudes()."
            )
            # wrap longitudes to [-180;+180[
            self.lons = utils.wrap_longitudes(lons)
        else:
            self.lons = lons

        self.cartesian_coords = None

    def intersection(self, other):
        """Return current area intersection polygon corners.

        *other* allows for potentially masked data in the corners.

        Parameters
        ----------
        other : object
            Instance of subclass of BaseDefinition

        Returns
        -------
        (corner1, corner2, corner3, corner4) : tuple of points
        """
        from pyresample.spherical_geometry import intersection_polygon

        # This was failing if all the corners of the
        #       area_definition fell inside the data box definition.
        #       watch for false positives
        # This DOES NOT WORK for over the pole...
        retcorners = intersection_polygon(self.corners, other.corners)
        allselfcornersin = False
        allothercornersin = False
        if not retcorners:
            # Only try these if intersection_polygon didn't return anything.
            for i in self.corners:
                if planar_point_inside(i, other.corners):
                    allselfcornersin = True
                else:
                    allselfcornersin = False
            for i in other.corners:
                if planar_point_inside(i, self.corners):
                    allothercornersin = True
                else:
                    allothercornersin = False

            if allselfcornersin:
                return self.corners
            if allothercornersin:
                return other.corners
        return retcorners

    def overlaps_minmaxlatlon(self, other):
        """Test current area overlaps *other* area.

        This is based solely on the min/max lat/lon of areas, assuming the
         boundaries to be along lat/lon lines.

        Parameters
        ----------
        other : object
            Instance of subclass of BaseDefinition

        Returns
        -------
        overlaps : bool
        """
        self_corners = get_2d_false_corners(self)
        other_corners = get_2d_false_corners(other)
        log.info("    Swath 2d False Corners: " + str(self_corners))
        log.info("    Other 2d False Corners: " + str(other_corners))

        for i in self_corners:
            if planar_point_inside(i, other_corners):
                return True
        for i in other_corners:
            if planar_point_inside(i, self_corners):
                return True
        return False

    @property
    def corners(self):
        """Return current area corners."""
        try:
            # Try to just set normal CoordinateDefinition corners
            #    (Which doesn't work with bad vals in corners)
            return super(CoordinateDefinition, self).corners
        except ValueError:
            # print '        Corners failed on CoordinateDefinition, try falsecorners'
            pass

        lons, lats = self.get_lonlats()

        # Determine which rows and columns contain good data
        rows = lons.any(axis=1)
        cols = lons.any(axis=0)

        # Get the minimum and maximum row and column that contain good data
        good_row_inds = np.where(~rows.mask)[0]
        min_row = good_row_inds.min()
        max_row = good_row_inds.max()

        good_col_inds = np.where(~cols.mask)[0]
        min_col = good_col_inds.min()
        max_col = good_col_inds.max()

        log.info(
            "    USING FALSE CORNERS!! setting corners. min row/col: "
            + str(min_row)
            + " "
            + str(min_col)
            + " "
            + "max row/col: "
            + str(max_row)
            + " "
            + str(max_col)
            + " "
            + "shape: "
            + str(lons.shape)
        )

        # from .spherical import SCoordinate as Coordinate
        # from .spherical import Arc
        from pyresample.spherical_geometry import Coordinate, Arc

        # Calculate the eight possible corners and produce arcs for each pair
        # Corners for top side
        # Right side was failing with Divide by Zero error for NCC data because there
        # was a single good point in the max_col.  Keep incrementing or decrementing
        # until good.min doesn't equal good.max
        good = np.where(~lons[min_row, :].mask)[0]
        tries = 0
        while tries < 20 and good.min() == good.max():
            # print 'good.min() can\'t equal good.max() for top side, incrementing
            # min_row! Would have failed with ZeroDivisionError before!'
            min_row += 1
            tries += 1
            good = np.where(~lons[min_row, :].mask)[0]
        top_corners = [
            Coordinate(*self.get_lonlat(min_row, good.min())),
            Coordinate(*self.get_lonlat(min_row, good.max())),
        ]
        top_arc = Arc(top_corners[0], top_corners[1])

        # Corners for bottom side
        good = np.where(~lons[max_row, :].mask)[0]
        tries = 0
        while tries < 20 and good.min() == good.max():
            # print 'good.min() can\'t equal good.max() for bottom side, decrementing
            # max_row! Would have failed with ZeroDivisionError before!'
            max_row -= 1
            tries += 1
            good = np.where(~lons[max_row, :].mask)[0]
        bot_corners = [
            Coordinate(*self.get_lonlat(max_row, good.min())),
            Coordinate(*self.get_lonlat(max_row, good.max())),
        ]
        bot_arc = Arc(bot_corners[0], bot_corners[1])

        # Corners for left side
        good = np.where(~lons[:, min_col].mask)[0]
        tries = 0
        while tries < 20 and good.min() == good.max():
            # print 'good.min() can\'t equal good.max() for left side, incrementing
            # min_col! Would have failed with ZeroDivisionError before!'
            min_col += 1
            tries += 1
            good = np.where(~lons[:, min_col].mask)[0]
        left_corners = [
            Coordinate(*self.get_lonlat(good.min(), min_col)),
            Coordinate(*self.get_lonlat(good.max(), min_col)),
        ]
        left_arc = Arc(left_corners[0], left_corners[1])

        # Corners for right side
        good = np.where(~lons[:, max_col].mask)[0]
        tries = 0
        while tries < 20 and good.min() == good.max():
            # print 'good.min() can\'t equal good.max() for right side, decrementing
            # max_col! Would have failed with ZeroDivisionError before!'
            max_col -= 1
            tries += 1
            good = np.where(~lons[:, max_col].mask)[0]
        right_corners = [
            Coordinate(*self.get_lonlat(good.min(), max_col)),
            Coordinate(*self.get_lonlat(good.max(), max_col)),
        ]
        right_arc = Arc(right_corners[0], right_corners[1])

        # Calculate the four false corners
        _corners = []
        # Top left false corner
        top_intersections = top_arc.intersections(left_arc)
        dists = [inter.distance(top_corners[0]) for inter in top_intersections]
        if dists[0] < dists[1]:
            _corners.append(top_intersections[0])
        else:
            _corners.append(top_intersections[1])
        # Top right false corner
        top_intersections = top_arc.intersections(right_arc)
        dists = [inter.distance(top_corners[1]) for inter in top_intersections]
        if dists[0] < dists[1]:
            _corners.append(top_intersections[0])
        else:
            _corners.append(top_intersections[1])
        # Bottom right false corner
        bot_intersections = bot_arc.intersections(right_arc)
        dists = [inter.distance(bot_corners[1]) for inter in bot_intersections]
        if dists[0] < dists[1]:
            _corners.append(bot_intersections[0])
        else:
            _corners.append(bot_intersections[1])
        # Bottom left false corner
        bot_intersections = bot_arc.intersections(left_arc)
        dists = [inter.distance(bot_corners[0]) for inter in bot_intersections]
        if dists[0] < dists[1]:
            _corners.append(bot_intersections[0])
        else:
            _corners.append(bot_intersections[1])
        return _corners

    def get_bounding_box_lonlats(self, npts=100):
        """Return lon/lats along bounding Arcs.

        Parameters
        ----------
        npts: int
            Number of points to return along each line

        Returns
        -------
        (top, right, bottom, left) : 4 tuples containing lists
                                    of len npts of lons/lats
        retval = (list(tplons),list(tplats)),
                 (list(rtlons),list(rtlats)),
                 (list(btlons),list(btlats)),
                 (list(ltlons),list(ltlats))

        eg for n=3
           ([tplon0,tplon1,tplon2],[tplat0,tplat1,tplat2]),
           ([rtlon0,rtlon1,rtlon2],[rtlat0,rtlat1,rtlat2]),
           ([btlon0,btlon1,btlon2],[btlat0,btlat1,btlat2]),
           ([ltlon0,ltlon1,ltlon2],[ltlat0,ltlat1,ltlat2]),
        """
        g = Geod(ellps="WGS84")

        # Top of bounding box
        # g.npts returns a list of tuples of lon/lat pairs
        #    [(lon0,lat0),(lon1,lat1),(lon2,lat2)]
        # zip reformats that into 2 tuples of lons and lats
        #    [(lon0,lon1,lon2),(lat0,lat1,lat2)]
        # list(tplons) returns list of lons
        #       [lon0,lon1,lon2]
        # list(tplats) returns list of lats
        #       [lat0,lat1,lat2]
        tplons, tplats = zip(
            *g.npts(
                self.corners[0].lon,
                self.corners[0].lat,
                self.corners[1].lon,
                self.corners[1].lat,
                npts,
                radians=True,
            )
        )
        # Right side of bounding box
        rtlons, rtlats = zip(
            *g.npts(
                self.corners[1].lon,
                self.corners[1].lat,
                self.corners[2].lon,
                self.corners[2].lat,
                npts,
                radians=True,
            )
        )
        # Bottom of bounding box
        btlons, btlats = zip(
            *g.npts(
                self.corners[2].lon,
                self.corners[2].lat,
                self.corners[3].lon,
                self.corners[3].lat,
                npts,
                radians=True,
            )
        )
        # Left side of bounding box
        ltlons, ltlats = zip(
            *g.npts(
                self.corners[3].lon,
                self.corners[3].lat,
                self.corners[0].lon,
                self.corners[0].lat,
                npts,
                radians=True,
            )
        )

        retval = [
            (list(tplons), list(tplats)),
            (list(rtlons), list(rtlats)),
            (list(btlons), list(btlats)),
            (list(ltlons), list(ltlats)),
        ]
        return retval


class PlanarPolygonDefinition(CoordinateDefinition):
    """Planar polygon definition."""

    def __init__(self, lons, lats, nprocs=1):
        if lons.shape != lats.shape:
            raise ValueError("lon and lat arrays must have same shape")
        elif lons.ndim > 2:
            raise ValueError("Only 1 and 2 dimensional swaths are allowed")

        if lons.shape == lats.shape and lons.dtype == lats.dtype:
            self.shape = lons.shape
            self.size = lons.size
            self.ndim = lons.ndim
            self.dtype = lons.dtype
        else:
            raise ValueError(
                (
                    "%s must be created with either "
                    "lon/lats of the same shape with same dtype"
                )
                % self.__class__.__name__
            )

        lats_type = type(lats)
        lons_type = type(lons)

        if lons_type != lats_type:
            raise TypeError("lons and lats must be of same type")
        elif lons is not None:
            if lons.shape != lats.shape:
                raise ValueError("lons and lats must have same shape")

        self.nprocs = nprocs

        # check the latitutes
        if lats is not None and ((lats.min() < -90.0 or lats.max() > +90.0)):
            # throw exception
            raise ValueError("Some latitudes are outside the [-90.;+90] validity range")
        else:
            self.lats = lats

        # check the longitudes
        if lons is not None and ((lons.min() < -180.0 or lons.max() >= +180.0)):
            # issue warning
            warnings.warn(
                "All geometry objects expect longitudes in the [-180:+180[ range. "
                "We will now automatically wrap your longitudes into [-180:+180[, "
                "and continue. "
                "To avoid this warning next time, use routine utils.wrap_longitudes()."
            )
            # wrap longitudes to [-180;+180[
            self.lons = utils.wrap_longitudes(lons)
        else:
            self.lons = lons

        self.cartesian_coords = None

    def get_bounding_box_lonlats(self, npts=100):
        """Return array of lon/lats along the bounding lat/lon lines.

        Parameters
        ----------
        npts: int
            Number of points to return along each line

        Returns
        -------
        (top, right, bottom, left) : 4 tuples containing lists
                                    of len npts of lons/lats
        retval = (list(tplons),list(tplats)),
                 (list(rtlons),list(rtlats)),
                 (list(btlons),list(btlats)),
                 (list(ltlons),list(ltlats))

        eg for n=3
           ([tplon0,tplon1,tplon2],[tplat0,tplat1,tplat2]),
           ([rtlon0,rtlon1,rtlon2],[rtlat0,rtlat1,rtlat2]),
           ([btlon0,btlon1,btlon2],[btlat0,btlat1,btlat2]),
           ([ltlon0,ltlon1,ltlon2],[ltlat0,ltlat1,ltlat2]),
        """
        # Top of bounding box
        tplons = np.linspace(self.corners[0].lon, self.corners[1].lon, npts)
        tplats = np.linspace(self.corners[0].lat, self.corners[1].lat, npts)
        # Right side of bounding box
        rtlons = np.linspace(self.corners[1].lon, self.corners[2].lon, npts)
        rtlats = np.linspace(self.corners[1].lat, self.corners[2].lat, npts)
        # Bottom of bounding box
        btlons = np.linspace(self.corners[2].lon, self.corners[3].lon, npts)
        btlats = np.linspace(self.corners[2].lat, self.corners[3].lat, npts)
        # Left side of bounding box
        ltlons = np.linspace(self.corners[3].lon, self.corners[0].lon, npts)
        ltlats = np.linspace(self.corners[3].lat, self.corners[0].lat, npts)

        retval = [
            (list(tplons), list(tplats)),
            (list(rtlons), list(rtlats)),
            (list(btlons), list(btlats)),
            (list(ltlons), list(ltlats)),
        ]
        return retval

    @property
    def corners(self):
        """Return corners."""
        # print '    In 2D false corners for: '+str(self.name)
        try:
            # print '        Corners already set, returning'
            return super(CoordinateDefinition, self).corners
        except ValueError:
            pass

        return get_2d_false_corners(self)

    def __contains__(self, point):
        """Idenfity if point inside the 4 corners of the current area.

        This DOES NOT use spherical geometry / great circle arcs.
        """
        corners = self.corners

        if isinstance(point, tuple):
            from pyresample.spherical_geometry import Coordinate

            retval = planar_point_inside(Coordinate(*point), corners)
        else:
            retval = planar_point_inside(point, corners)

        # print '        retval from FALSE CORNERS contains '+str(retval)

        return retval

    def intersection(self, other):
        """Return current area intersection polygon corners against other.

        Parameters
        ----------
        other : object
            Instance of subclass of BaseDefinition

        Returns
        -------
        (corner1, corner2, corner3, corner4) : tuple of points
        """
        self_corners = self.corners

        other_corners = get_2d_false_corners(other)

        # shell()

        return planar_intersection_polygon(self_corners, other_corners)

    def overlaps_minmaxlatlon(self, other):
        """Determine if overlaps."""
        log.info("PlanarPolygonDefinition overlaps_minmaxlatlon")
        return self.overlaps(other)

    def overlaps(self, other):
        """Test if the current area overlaps the *other* area.

        This is based
        solely on the corners of areas, assuming the boundaries to be straight
        lines.

        Parameters
        ----------
        other : object
            Instance of subclass of BaseDefinition

        Returns
        -------
        overlaps : bool
        """
        self_corners = self.corners
        other_corners = get_2d_false_corners(other)

        log.info("    PlanarPolygon Overlaps Self False Corners: " + str(self_corners))
        log.info(
            "    PlanarPolygon Overlaps Other False Corners: " + str(other_corners)
        )

        # Previously just did if i in other or if i in self.
        # This does not take 2d_false_corners into account
        # when doing i in *area_definition* (because it uses
        # area_definition.__contains__, which does not use
        # planar_point_inside, but spherical point_inside.
        for i in self_corners:
            if planar_point_inside(i, other_corners):
                log.info("    Point " + str(i) + " in other")
                return True
        for i in other_corners:
            if planar_point_inside(i, self_corners):
                log.info("    Point " + str(i) + " in self")
                return True

        self_line1 = Line(self_corners[0], self_corners[1])
        self_line2 = Line(self_corners[1], self_corners[2])
        self_line3 = Line(self_corners[2], self_corners[3])
        self_line4 = Line(self_corners[3], self_corners[0])

        other_line1 = Line(other_corners[0], other_corners[1])
        other_line2 = Line(other_corners[1], other_corners[2])
        other_line3 = Line(other_corners[2], other_corners[3])
        other_line4 = Line(other_corners[3], other_corners[0])

        for i in (self_line1, self_line2, self_line3, self_line4):
            for j in (other_line1, other_line2, other_line3, other_line4):
                if i.intersects(j):
                    return True
        return False


class Line(object):
    """A Line between two lat/lon points."""

    start = None
    end = None

    def __init__(self, start, end):
        """Initialize Line."""
        self.start, self.end = start, end

    def __eq__(self, other):
        """Test two lines equal."""
        if (
            abs(self.start.lon - other.start.lon) < EPSILON
            and abs(self.end.lon - other.end.lon) < EPSILON
            and abs(self.start.lat - other.start.lat) < EPSILON
            and abs(self.end.lat - other.end.lat) < EPSILON
        ):
            return 1
        return 0

    def __ne__(self, other):
        """Test two lines not equal."""
        return not self.__eq__(other)

    def __str__(self):
        """Return string."""
        return str(self.start) + " -> " + str(self.end)

    def __repr__(self):
        """Return representation."""
        return str(self.start) + " -> " + str(self.end)

    def intersects(self, other_line):
        """Test two lines intersect.

        Says if two lines defined by the current line and the *other_line*
        intersect. A line is defined as the shortest tracks between two points.
        """
        intpt = self.intersection(other_line)
        return bool(intpt)

    def intersection(self, other):
        """Identify intersection between two lines.

        Says where, if two lines defined by the current line and the
        *other_line* intersect.
        """
        log.info("self: " + str(self) + " other: " + str(other))
        if self == other:
            # Used to be return True, that is definitely not right (expects Coordinate)
            # Do we want start or end ? Does it matter? Lines are the same, everything
            # is an intersection.
            return self.start
        # If any of the start/end points match, return that point.
        if self.end == other.start or self.end == other.end:
            return self.end
        if self.start == other.start or self.start == other.end:
            return self.start

        # Line equation: y = mx + b
        # m = (y2-y1)/(x2-x1)
        # B_self = y - M_self*x
        # Pick any x/y on the line - try end point
        # B_self = self.end.lat - M_self*self.end.lon
        # B_other = other.end.lat - M_self*self.end.lon
        from pyresample.spherical_geometry import Coordinate

        selfendlon = self.end.lon
        selfstartlon = self.start.lon
        otherendlon = other.end.lon
        otherstartlon = other.start.lon
        # Not sure if this is necessary, or good...
        #        if self.end.lon < 0:
        #            selfendlon = self.end.lon + 2*math.pi
        #        if self.start.lon < 0:
        #            selfstartlon = self.start.lon + 2*math.pi
        #        if other.end.lon < 0:
        #            otherendlon = other.end.lon + 2*math.pi
        #        if other.start.lon < 0:
        #            otherstartlon = other.start.lon + 2*math.pi

        log.info(
            "    self lons: "
            + str(math.degrees(selfstartlon))
            + " "
            + str(math.degrees(selfendlon))
            + " other lons: "
            + str(math.degrees(otherstartlon))
            + " "
            + str(math.degrees(otherendlon))
        )

        # If both vertical, will be no intersection
        if (
            abs(selfendlon - selfstartlon) < EPSILON
            and abs(otherendlon - otherstartlon) < EPSILON
        ):
            log.info("    Both vertical, no intersection")
            return None
        # If self is vertical, but not parallel, intersection will be selfstartlon
        # and lat = Mother*lon+B_other
        if abs(selfendlon - selfstartlon) < EPSILON:
            lon = selfstartlon
            M_other = (other.end.lat - other.start.lat) / (otherendlon - otherstartlon)
            B_other = other.end.lat - M_other * otherendlon
            lat = M_other * lon + B_other
            log.info("    self is vertical")
            # Make sure it falls within the segment and not outside.
            # Previously was only checking lat, need to
            # also check lon or opposite side of world would match
            if (
                lat > min([self.end.lat, self.start.lat])
                and lat < max([self.end.lat, self.start.lat])
                and lon > min([otherendlon, otherstartlon])
                and lon < max([otherendlon, otherstartlon])
            ):
                log.info("        and intersects")
                # Apparently Coordinate takes degrees ??? And must be -180 to 180 ?!
                # MLS use wrap_longitudes?
                if lon > math.pi:
                    lon -= 2 * math.pi
                return Coordinate(math.degrees(lon), math.degrees(lat))
            else:
                return None
        # same for other
        if abs(otherendlon - otherstartlon) < EPSILON:
            lon = otherstartlon
            M_self = (self.end.lat - self.start.lat) / (selfendlon - selfstartlon)
            B_self = self.end.lat - M_self * selfendlon
            lat = M_self * lon + B_self
            log.info("    other is vertical")
            # Make sure it falls within the segment and not outside.
            # Previously was only checking lat, need to
            # also check lon or opposite side of world would match
            if (
                lat > min([other.end.lat, other.start.lat])
                and lat < max([other.end.lat, other.start.lat])
                and lon > min([selfendlon, selfstartlon])
                and lon < max([selfendlon, selfstartlon])
            ):
                log.info("        and intersects")
                # Apparently Coordinate takes degrees ??? And must be -180 to 180 ?!
                # MLS Use wrap_longitudes?
                if lon > math.pi:
                    lon -= 2 * math.pi
                return Coordinate(math.degrees(lon), math.degrees(lat))
            else:
                return None

        # Get slopes of the lines
        M_self = (self.end.lat - self.start.lat) / (selfendlon - selfstartlon)
        M_other = (other.end.lat - other.start.lat) / (otherendlon - otherstartlon)

        # If they are parallel, no intersection
        if (M_self - M_other) < EPSILON:
            log.info("    self and other are parallel, no intersection")
            return None

        # Get the y-intercepts of the lines
        B_self = self.end.lat - M_self * selfendlon
        B_other = other.end.lat - M_other * otherendlon

        # Solve the equation
        # y=m1x+b1 and y=m2x+b2, equate y's so m1x+b1=m2x+b2, x = (b1-b2)/(m2-m1)
        # equate x's so x=(y-b1)/m1=(y-b2)/m2, y = (b1m2-b2m1)/(m2-m1)
        lon = (B_self - B_other) / (M_other - M_self)
        lat = (B_self * M_other - B_other * M_self) / (M_other - M_self)

        # Make sure lat/lon intersects within the line segment, and not outside.
        if (
            lat > min([other.end.lat, other.start.lat])
            and lat < max([other.end.lat, other.start.lat])
            and lon > min([otherendlon, otherstartlon])
            and lon < max([otherendlon, otherstartlon])
            and lat > min([self.end.lat, self.start.lat])
            and lat < max([self.end.lat, self.start.lat])
            and lon > min([selfendlon, selfstartlon])
            and lon < max([selfendlon, selfstartlon])
        ):
            log.info("    self and other intersect within segment")
            # Apparently Coordinate takes degrees ??? And must be -180 to 180 ?!
            # MLS use wrap longitudes?
            if lon > math.pi:
                lon -= 2 * math.pi
            return Coordinate(math.degrees(lon), math.degrees(lat))
        else:
            log.info("    self and other intersect, but not within segment")
            return None


def get_2d_false_corners(box_def):
    """Identify false corners."""
    # print '    In 2D false corners for: '+str(box_def.name)

    min_row = 0
    max_row = -1
    min_col = 0
    max_col = -1
    side1 = box_def.get_lonlats(data_slice=(min_row, slice(None)))
    side2 = box_def.get_lonlats(data_slice=(slice(None), max_col))
    side3 = box_def.get_lonlats(data_slice=(max_row, slice(None)))
    side4 = box_def.get_lonlats(data_slice=(slice(None), min_col))

    tries = 0
    while (
        tries < 500
        and np.ma.count(box_def.get_lonlats(data_slice=(min_row, slice(None)))[1]) < 10
    ):
        min_row += 1
        tries += 1
    if tries:
        side1 = box_def.get_lonlats(data_slice=(min_row + 1, slice(None)))
        log.info(
            "Needed some data in side 1, incremented slice number "
            + str(tries)
            + " times. Now have "
            + str(np.ma.count(side1[1]))
            + " valid of "
            + str(np.ma.count(side1[1].mask))
        )

    tries = 0
    while (
        tries < 500
        and np.ma.count(box_def.get_lonlats(data_slice=(slice(None), max_col))[0]) < 10
    ):
        max_col -= 1
        tries += 1
    if tries:
        side2 = box_def.get_lonlats(data_slice=(slice(None), max_col - 1))
        log.info(
            "Needed some data in side 2, decremented slice number "
            + str(tries)
            + " times. Now have "
            + str(np.ma.count(side2[0]))
            + " valid of "
            + str(np.ma.count(side2[0].mask))
        )

    tries = 0
    while (
        tries < 500
        and np.ma.count(box_def.get_lonlats(data_slice=(max_row, slice(None)))[0]) < 10
    ):
        max_row -= 1
        tries += 1
    if tries:
        side3 = box_def.get_lonlats(data_slice=(max_row - 1, slice(None)))
        log.info(
            "Needed some data in side 3, decremented slice number "
            + str(tries)
            + " times. Now have "
            + str(np.ma.count(side3[0]))
            + " valid of "
            + str(np.ma.count(side3[0].mask))
        )

    tries = 0
    while (
        tries < 500
        and np.ma.count(box_def.get_lonlats(data_slice=(slice(None), min_col))[1]) < 10
    ):
        min_col += 1
        tries += 1
    if tries:
        side4 = box_def.get_lonlats(data_slice=(slice(None), min_col + 1))
        log.info(
            "Needed some data in side 4, incremented slice number "
            + str(tries)
            + " times. Now have "
            + str(np.ma.count(side4[1]))
            + " valid of "
            + str(np.ma.count(side4[1].mask))
        )

    # shell()

    # These all need to maintain mask.
    selflons = np.ma.concatenate((side1[0], side2[0], side3[0], side4[0]))
    selflons = np.ma.where(selflons < 0, selflons + 360, selflons)
    # MLS use wrap_longitudes? Figure out prime meridian vs dateline...
    # if side4[0].min() > side2[0].max():
    #    selflons = np.ma.where(selflons<0,selflons+360,selflons)
    selflats = np.ma.concatenate((side1[1], side2[1], side3[1], side4[1]))

    # self_corners = self.corners
    # other_corners = other.corners
    minlon = selflons.min()
    maxlon = selflons.max()
    # MLS use wrap_longitudes?
    if minlon > 180:
        minlon -= 360
    if maxlon > 180:
        maxlon -= 360
    minlat = selflats.min()
    maxlat = selflats.max()

    # print 'IN PlanarPolygonDefinition CORNERS for '+box_def.name+\
    #    ' min/max lat min/max lon:'+\
    #    str(minlat)+' '+str(maxlat)+' '+str(minlon)+' '+str(maxlon)

    from pyresample.spherical_geometry import Coordinate

    return [
        Coordinate(minlon, maxlat),
        Coordinate(maxlon, maxlat),
        Coordinate(maxlon, minlat),
        Coordinate(minlon, minlat),
    ]


def planar_intersection_polygon(area_corners, segment_corners):
    """Get the intersection polygon between two areas."""
    # First test each
    lons = np.array([])
    lats = np.array([])
    for segment_corner in segment_corners:
        if planar_point_inside(segment_corner, area_corners):
            currlon = segment_corner.lon
            # MLS use wrap_longitudes?
            if currlon < 0:
                currlon += 2 * math.pi
            lons = np.concatenate((lons, [currlon]))
            lats = np.concatenate((lats, [segment_corner.lat]))
            log.info("Adding intersection from segment " + str(segment_corner))
    for area_corner in area_corners:
        if planar_point_inside(area_corner, segment_corners):
            currlon = area_corner.lon
            # MLS use wrap_longitudes?
            if currlon < 0:
                currlon += 2 * math.pi
            lons = np.concatenate((lons, [currlon]))
            lats = np.concatenate((lats, [area_corner.lat]))
            log.info("Adding intersection from area " + str(area_corner))

    area_line1 = Line(area_corners[0], area_corners[1])
    area_line2 = Line(area_corners[1], area_corners[2])
    area_line3 = Line(area_corners[2], area_corners[3])
    area_line4 = Line(area_corners[3], area_corners[0])

    segment_line1 = Line(segment_corners[0], segment_corners[1])
    segment_line2 = Line(segment_corners[1], segment_corners[2])
    segment_line3 = Line(segment_corners[2], segment_corners[3])
    segment_line4 = Line(segment_corners[3], segment_corners[0])

    for i in (area_line1, area_line2, area_line3, area_line4):
        for j in (segment_line1, segment_line2, segment_line3, segment_line4):
            intersect = i.intersection(j)
            if intersect:
                log.info("Adding actual intersection " + str(intersect))
                currlon = intersect.lon
                # MLS use wrap_longitudes?
                if intersect.lon < 0:
                    currlon += 2 * math.pi
                lons = np.concatenate((lons, [currlon]))
                lats = np.concatenate((lats, [intersect.lat]))

    minlon = math.degrees(lons.min())
    maxlon = math.degrees(lons.max())
    minlat = math.degrees(lats.min())
    maxlat = math.degrees(lats.max())
    # Coordinate MUST be between -180 and 180
    # MLS use wrap_longitudes?
    if minlon > 180:
        minlon -= 180
    if maxlon > 180:
        maxlon -= 180
    from pyresample.spherical_geometry import Coordinate

    return [
        Coordinate(minlon, maxlat),
        Coordinate(maxlon, maxlat),
        Coordinate(maxlon, minlat),
        Coordinate(minlon, minlat),
    ]


#    for seg_pt in seg_pts_in_area:
#
#
#
#
#
# def planar_point_inside(point, boxdef):
def planar_point_inside(point, corners):
    """Identify point inside 4 corners.

    This DOES NOT USE great circle arcs as area
    boundaries.
    """
    #    lons = boxdef.get_lonlats()[0]
    lons = np.ma.array([corn.lon for corn in corners])
    lats = np.ma.array([corn.lat for corn in corners])
    # MLS use wrap_longitudes?
    lons = np.ma.where(lons < 0, lons + 2 * math.pi, lons)

    #    lats = boxdef.get_lonlats()[1]
    #    corners = boxdef.corners
    minlon = lons.min()
    maxlon = lons.max()
    minlat = lats.min()
    maxlat = lats.max()
    # MLS use wrap_longitudes?
    if point.lon < 0:
        point.lon += 2 * math.pi
    #    print '    IN PlanarPolygonDefinition point_inside!!! '+\
    #        ' point: '+str(point)+' '+str(math.degrees(minlat))+' '+
    #                 str(math.degrees(maxlat))+' '+str(math.degrees(minlon))+' '+
    #                 str(math.degrees(maxlon))
    #        ' point: '+str(point)+'\n'+\
    #        'c0 '+str(corners[0])+'\n'+\
    #        'c1 '+str(corners[1])+'\n'+\
    #        'c2 '+str(corners[2])+'\n'+\
    #        'c3 '+str(corners[3])+'\n'+\
    #        str(minlat)+' '+str(maxlat)+' '+str(minlon)+' '+str(maxlon)
    # MLS 20160405 NOTE point prints degrees for str, but point.lon and point.lat are
    # stored as radians.
    # minlon/maxlon also radians.
    # This is why big sectors were failing, after fixing the
    # "other side of the world" problem.
    # Also, Coordinate takes degrees when passing it a lat lon
    if minlon < point.lon < maxlon and minlat < point.lat < maxlat:
        return True
    return False


def _get_slice(segments, shape):
    """Segment a 1D or 2D array."""
    if not (1 <= len(shape) <= 2):
        raise ValueError("Cannot segment array of shape: %s" % str(shape))
    else:
        size = shape[0]
        slice_length = np.ceil(float(size) / segments)
        start_idx = 0
        end_idx = slice_length
        while start_idx < size:
            if len(shape) == 1:
                yield slice(start_idx, end_idx)
            else:
                yield (slice(start_idx, end_idx), slice(None))
            start_idx = end_idx
            end_idx = min(start_idx + slice_length, size)


def _flatten_cartesian_coords(cartesian_coords):
    """Flatten array to (n, 3) shape."""
    shape = cartesian_coords.shape
    if len(shape) > 2:
        cartesian_coords = cartesian_coords.reshape(shape[0] * shape[1], 3)
    return cartesian_coords


def _get_highest_level_class(obj1, obj2):
    """Get highest level class."""
    if not issubclass(obj1.__class__, obj2.__class__) or not issubclass(
        obj2.__class__, obj1.__class__
    ):
        raise TypeError(
            "No common superclass for %s and %s" % (obj1.__class__, obj2.__class__)
        )

    if obj1.__class__ == obj2.__class__:
        klass = obj1.__class__
    elif issubclass(obj1.__class__, obj2.__class__):
        klass = obj2.__class__
    else:
        klass = obj1.__class__
    return klass
