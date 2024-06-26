import hou
import logging
from pxr import Usd, UsdGeom


def get_startprim(cur_stage: Usd.Stage, cur_node: hou.LopNode, param: str) -> str:
    """
    Takes the primpath passed into the parent node and returns the USD primitive at the given path.



    Args:
        cur_stage (Usd.Stage): Current USD stage.
        cur_node (hou.LopNode): Current LOP node.
        param (str): Primpath to evaluate.



    Returns:
        start_prim (Usd.Prim): Primitive at path.



    """
    prim_pattern = cur_node.parm(param).eval()
    start_prim = cur_stage.GetPrimAtPath(prim_pattern)

    return start_prim


def get_child_payloads(cur_prim: Usd.Prim) -> list:
    """
    Takes a Usd.Prim and finds all child prims with payloads i.e. prims likely to have an extentsHint attribute for their payload extents.



    Args:
        cur_prim (Usd.Prim): Prim to evaluate.



    Returns:
        prims_with_payloads (list): List containing all children of cur_prim with child payloads.



    """
    iterator = iter(Usd.PrimRange(cur_prim))
    prims_with_payloads = []

    for child in iterator:
        if child.HasPayload():
            prims_with_payloads.append(child)
        # elif child.IsInstance():
        #     found_payloads.append(child.GetChild('geo'))

    return prims_with_payloads


def get_extents(cur_prim: Usd.Prim, total_prims: list) -> list:
    """
    From LOP node > setextents.
    Takes a current Usd.Prim and a list of Usd.Prims. Iterates through the current Usd.Prim children and recursively checks for boundable prims, returning the max/min bounding region.



    Args:
        cur_prim (Usd.Prim): Prim to evaluate.
        total_prims (list): All child prims found.



    Returns:
        extent (list): List containing bounding regions of the current prim, stored as Gf.Vec3d objects.



    """
    time = Usd.TimeCode.Default()

    boundable = UsdGeom.Boundable(cur_prim)
    if boundable:
        if cur_prim in total_prims:
            extent = UsdGeom.Boundable.ComputeExtentFromPlugins(boundable, time)
        else:
            cache = UsdGeom.BBoxCache(time, [UsdGeom.Tokens.default_])
            bounds = cache.ComputeLocalBound(cur_prim)
            minmax = bounds.GetRange()
            extent = [minmax.GetMin(), minmax.GetMax()]
    else:
        extent = None
        for child in cur_prim.GetAllChildren():
            childextent = get_extents(child, total_prims)
            if not childextent:
                continue
            extent = childextent
        if extent:
            cache = UsdGeom.BBoxCache(time, [UsdGeom.Tokens.default_])
            bounds = cache.ComputeLocalBound(cur_prim)
            minmax = bounds.GetRange()
            extent = [minmax.GetMin(), minmax.GetMax()]
    return extent


def check_extents_data(prim_data: dict) -> "None":
    """
    Iterates through a dictionary containing a list of 2 tuples for every key and compares them - if a mismatch is found, an exception is raised and a warning printed to the console.



    Args:
        prim_date (dict): In the format {Usd.Prim: [tuple, tuple]}



    Returns:
        None.



    """
    mismatched_data = []

    for prim, extent in prim_data.items():
        try:
            if extent[0] == extent[1]:
                raise ValueError(f"Data mismatch on {prim}")
        except ValueError:
            mismatched_data.append(prim)

    if mismatched_data:
        elements_string = ", ".join(
            f"\n{element.GetPath()}" for element in mismatched_data
        )
        warning_message = f"Detected extents mismatch at: {elements_string}\nThese prims may require extent recalculation."
        print(warning_message)
        # logging.warning(warning_message)


def format_prim_path(cur_prim: Usd.Prim) -> str:
    """
    Takes a prim and formats its' primpath to just 2 ancestors of the payload.



    Args:
        cur_prim (Usd.Prim): The prim to evaluate.



    Returns:
        formatted_path (str): A truncated version of the primpath.



    """
    path = str(cur_prim.GetPath())

    components = path.split("/")
    select_components = components[-2:-1]
    truncate_selection = [item.rsplit("_", 1)[0] for item in select_components]
    formatted_path = "/".join(truncate_selection)

    return formatted_path


def main(cur_node: hou.LopNode) -> "None":
    """
    Takes a LOP node with a primpattern parm and recomputes the extents of all subgeo of the given primpattern, comparing values with extentsHint attributes stored on the prim. Prints a warning to the console if mismatched data is found.



    Args:
        cur_node (hou.LopNode): Current LOP node, passed in by the node's python modules for example.



    Returns:
        None



    """
    print("Refresh.")

    node = cur_node
    stage = node.inputs()[0].stage()

    start_prim = get_startprim(stage, node, "primpattern")
    total_prims = get_child_payloads(start_prim)

    caught_prims = {}

    for prim in total_prims:
        prim_extentsHint = prim.GetAttribute("extentsHint").Get(hou.frame())
        if prim_extentsHint:
            extentHints_tuple = [tuple(vec) for vec in prim_extentsHint]
            round_extentHints = [
                (round(x, 7), round(y, 7), round(z, 7)) for x, y, z in extentHints_tuple
            ]

            extents = get_extents(prim, total_prims)
            round_extents = [
                (round(x, 7), round(y, 7), round(z, 7)) for x, y, z in extents
            ]
            caught_prims[prim] = [round_extentHints, round_extents]

    check_extents_data(caught_prims)
