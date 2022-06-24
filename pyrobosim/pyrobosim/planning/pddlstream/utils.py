"""
Utilities to connect world models with PDDLStream.
"""

import os

from ..actions import TaskAction, TaskPlan
from ...utils.general import get_data_folder
from ...utils.motion import Path


def get_default_domains_folder():
    """
    Returns the default path to the folder containing PDDLStream domains.

    :return: Path to domains folder.
    :rtype: str
    """
    return os.path.join(get_data_folder(), "pddlstream", "domains")


def world_to_pddlstream_init(world):
    """
    Converts a world representation object to a PDDLStream compatible
    initial condition specification.

    :param world: World model.
    :type world: :class:`pyrobosim.core.world.World`
    :return: PDDLStream compatible initial state representation. 
    :rtype: list[tuple]
    """

    # Start with the robot initial conditions
    robot = world.robot
    init_loc = robot.location
    if not init_loc:
        init_loc = world.get_location_from_pose(robot.pose)
    init = [("Robot", robot),
            ("HandEmpty", robot), 
            ("At", robot, init_loc),
            ("Pose", robot.pose),
            ("AtPose", robot, robot.pose)]

    # Loop through all the locations and their relationships.
    # This includes rooms and object spawns (which are children of locations).
    for room in world.rooms:
        init.append(("Room", room))
        init.append(("Location", room))
    loc_categories = set()
    for loc in world.locations:
        for spawn in loc.children:
            init.append(("Location", spawn))
            init.append(("Is", spawn, loc.category))
            init.append(("AtRoom", spawn, loc.parent))
        loc_categories.add(loc.category)
    for loc_cat in loc_categories:
        init.append(("Type", loc_cat))

    # Loop through all the objects and their relationships.
    obj_categories = set()
    for obj in world.objects:
        init.append(("Obj", obj))
        init.append(("Is", obj, obj.category))
        # If the object is the current manipulated object, change the robot state.
        # Otherwise, the object is at its parent location.
        if robot.manipulated_object == obj:
            init.remove(("HandEmpty", robot))
            init.append(("Holding", robot, obj))
        else:
            init.append(("At", obj, obj.parent))
        obj_categories.add(obj.category)
    for obj_cat in obj_categories:
        init.append(("Type", obj_cat))        

    return init


def pddlstream_solution_to_plan(solution):
    """
    Converts the output plan of a PDDLStream solution to a plan
    list compatible with plan execution infrastructure.

    :param: PDDLStream compatible initial state representation. 
    :type: list[tuple]
    :return: Task plan object.
    :rtype: :class:`pyrobosim.planning.actions.TaskPlan`
    """
    # Unpack the PDDLStream solution and handle the None case
    plan, total_cost, _ = solution
    if plan is None or len(plan)==0:
        return None

    plan_out = TaskPlan(actions=[])
    for act_pddl in plan:
        # Convert the PDDL action to a TaskAction
        act = TaskAction(act_pddl.name)
        # Parse a NAVIGATE action
        if act.type == "navigate":
            act.source_location = act_pddl.args[1]
            act.target_location = act_pddl.args[2]
            # Search for a path.
            for arg in act_pddl.args[3:]:
                if isinstance(arg, Path):
                    act.path = arg
        # Parse a PICK or PLACE action
        elif act.type == "pick" or act.type == "place":
            act.object = act_pddl.args[1]
            act.target_location = act_pddl.args[2]
            # If a pick/place pose is specified, add it.
            if len(act_pddl.args) > 3:
                act.pose = act_pddl.args[3]

        # Add the action to the task plan
        plan_out.actions.append(act)

    # TODO: Find a way to get the individual action costs from PDDLStream.
    # For now, just set the total cost, which is readily available from the solution.
    plan_out.total_cost = total_cost
    return plan_out
