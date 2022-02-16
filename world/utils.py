import numpy as np
from shapely.geometry import CAP_STYLE, JOIN_STYLE

##################
# Pose Utilities #
##################


class Pose:
    """ Represents a 2.5D (X, Y, Z, yaw) pose """

    def __init__(self, x=0.0, y=0.0, z=0.0, yaw=0.0):
        self.x = x
        self.y = y
        self.z = z
        self.yaw = wrap_angle(yaw)

    def __repr__(self):
        return f"Pose: [x={self.x:.2f}, y={self.y:.2f} z={self.z:.2f} yaw={self.yaw:.2f}]"


def get_angle(p1, p2):
    """ 
    Basic utility for getting angle between 2D points.
    The convention is p2 relative to p1.
    """
    return wrap_angle(np.arctan2(p2[1]-p1[1], p2[0]-p1[0]))


def get_distance(p1, p2):
    """ Basic utility for getting distance between points. """
    sqrs = [(i-j)**2 for i, j in zip(p1, p2)]
    return np.sqrt(sum(sqrs))


def get_bearing_range(p1, p2):
    """ 
    Gets bearing and range between 2 points p1 and p2.
    The convention is p2 relative to p1.
    """
    rng = get_distance(p1, p2)
    bear = get_angle(p1, p2)
    return (bear, rng)


def wrap_angle(ang):
    """ Wraps an angle in the range [-pi, pi]. """
    while ang < -np.pi:
        ang += 2*np.pi
    while ang > np.pi:
        ang -= 2*np.pi
    return ang

#####################
# Polygon Utilities #
#####################


def add_coords(coords, offset):
    """
    Adds an offset (x,y) vector to a Shapely compatible list 
    of coordinate tuples

    Args:
        coords: A list of coordinate tuples representing the polygon
        offset: An (x,y) offset vector list or tuple
    """
    x, y = offset
    return [(c[0]+x, c[1]+y) for c in coords]


def box_to_coords(dims=[1, 1], origin=[0, 0], ang=0):
    """ 
    Converts box dimensions and origin to a Shapely compatible 
    list of coordinate tuples.

    Args:
        dims (list): The box dimensions [width, height]
        origin (list): The box origin [x, y]
        ang (float): The angle (in radians) to rotate the box

    Returns:
        coords: A list of coordinate tuples representing the box

    Examples:
        >>> coords = box_to_coords(dims=[2.5,2.5], origin=[1,2])
    """
    x, y = origin
    w, h = dims
    coords = [
        rot2d((-0.5*w, -0.5*h), ang),
        rot2d((0.5*w, -0.5*h), ang),
        rot2d((0.5*w,  0.5*h), ang),
        rot2d((-0.5*w,  0.5*h), ang),
    ]
    coords.append(coords[0])
    coords = add_coords(coords, (x, y))
    return coords


def get_polygon_centroid(poly):
    """ Gets a Shapely polygon centroid as a list """
    return list(poly.centroid.coords)[0]


def inflate_polygon(poly, radius):
    """ 
    Inflates a Shapely polygon with options preconfigured for 
    this world modeling framework.
    """
    return poly.buffer(radius,
                       cap_style=CAP_STYLE.flat,
                       join_style=JOIN_STYLE.mitre)


def rot2d(vec, ang):
    """ Rotates a 2-element vector `vec` by an angle `ang` """
    v = np.array([[vec[0]],
                  [vec[1]]])
    M = np.array([[np.cos(ang), -np.sin(ang)],
                  [np.sin(ang),  np.cos(ang)]])
    v_tf = np.matmul(M, v)
    return v_tf.flatten().tolist()
