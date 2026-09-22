"""Small ``kdl_parser_py`` compatible URDF-to-KDL adapter.

ROS 1 commonly exposes ``kdl_parser_py.urdf``.  The lesson code imported by
``check_fk_with_mujoco.py`` expects ``kdl_parser.urdf`` instead, so this module
provides the two functions it uses without requiring another package install.
"""

import PyKDL
from urdf_parser_py.urdf import URDF


def treeFromFile(filename):
    """Parse a URDF file and return ``(success, PyKDL.Tree)``."""
    return treeFromUrdfModel(URDF.from_xml_file(filename))


def treeFromUrdfModel(robot):
    """Build a ``PyKDL.Tree`` from a ``urdf_parser_py`` robot model."""
    root = robot.get_root()
    tree = PyKDL.Tree(root)
    links = {link.name: link for link in robot.links}
    joints = {joint.name: joint for joint in robot.joints}

    def add_children(parent_link):
        for joint_name, child_link in robot.child_map.get(parent_link, []):
            joint = joints[joint_name]
            segment = _to_kdl_segment(joint, links[child_link])
            if not tree.addSegment(segment, parent_link):
                return False
            if not add_children(child_link):
                return False
        return True

    return add_children(root), tree


def _to_kdl_segment(joint, child_link):
    frame = _to_kdl_frame(joint.origin)
    return PyKDL.Segment(child_link.name, _to_kdl_joint(joint, frame), frame)


def _to_kdl_joint(joint, frame):
    if joint.type == "fixed":
        return PyKDL.Joint(joint.name, PyKDL.Joint.Fixed)

    axis_xyz = joint.axis if joint.axis is not None else [1.0, 0.0, 0.0]
    axis = frame.M * PyKDL.Vector(*axis_xyz)

    if joint.type in ("revolute", "continuous"):
        return PyKDL.Joint(joint.name, frame.p, axis, PyKDL.Joint.RotAxis)
    if joint.type == "prismatic":
        return PyKDL.Joint(joint.name, frame.p, axis, PyKDL.Joint.TransAxis)

    raise ValueError(f"Unsupported URDF joint type for KDL conversion: {joint.type}")


def _to_kdl_frame(origin):
    if origin is None:
        return PyKDL.Frame.Identity()

    xyz = origin.xyz if origin.xyz is not None else [0.0, 0.0, 0.0]
    rpy = origin.rpy if origin.rpy is not None else [0.0, 0.0, 0.0]
    return PyKDL.Frame(PyKDL.Rotation.RPY(*rpy), PyKDL.Vector(*xyz))
