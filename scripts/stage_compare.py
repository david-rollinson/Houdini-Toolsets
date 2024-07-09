import hou
import pxr
from pxr import Sdf, Usd, UsdGeom, Vt, Gf

# This tool is in development to catch bad attributes added by ANIM USD layers that can cause crashing in Houdini. It takes 2 USD stages as HDA input.
# Given a primitive primpattern, it searches all child prims for array/list type attributes and compares their size to the same primitive attribute on the other stage.


def get_startprim(start_layer: Usd.Stage, cur_node: hou.LopNode, param: str) -> str:
    # Get the prim pattern for the prim we want to check.
    prim_pattern = cur_node.parm(param).eval()  # pass in 'primpattern'.
    start_prim = start_layer.GetPrimAtPath(prim_pattern)
    return start_prim


def find_child_prims(cur_prim: Usd.Prim) -> []:
    iterator = iter(Usd.PrimRange(cur_prim))
    # 'Predicate' selection as Geometry i.e. metadata check prim inherits UsdGeomGprim base class.
    total_geometry = [
        {"geometry": prim} for prim in iterator if prim.IsA(UsdGeom.Gprim)
    ]
    return total_geometry


def find_prim_attribute_arrays(cur_prim: Usd.Prim) -> {}:
    total_attribs = {}
    num_attribs = len(cur_prim.GetAttributes())
    print(f"Numattribs: {num_attribs}")
    for i, attribute in enumerate(cur_prim.GetAttributes()):
        attribute_value = attribute.Get(hou.frame())
        # Type check the attribute. If it is of an array type, add the attribute to the list.
        if (
            isinstance(attribute_value, pxr.Vt.IntArray)
            | isinstance(attribute_value, pxr.Vt.Vec2fArray)
            | isinstance(attribute_value, pxr.Vt.Vec3fArray)
            | isinstance(attribute_value, pxr.Vt.FloatArray)
            | isinstance(attribute_value, pxr.Gf.Vec3f)
        ):
            attribute_length = len(attribute_value)
            attribute_name = attribute.GetName()
            total_attribs[attribute_name] = [attribute_length]
    return total_attribs


def compare_attributes(
    compare_stage: Usd.Stage, cur_prim: Usd.Prim, attribute: str
) -> int:
    # Return the prim on the comparison Stage.
    prim = compare_stage.GetPrimAtPath(cur_prim.GetPath())
    # Check prim validity on compare stage.
    if not prim.IsValid():
        print("Prim is invalid.")
    return len(prim.GetAttribute(attribute).Get(hou.frame()))


def main(cur_node: hou.LopNode) -> "None":
    # Set the node and stages to receive data from.
    node = cur_node
    origin_stage = node.inputs()[0].stage()
    compare_stage = node.inputs()[1].stage()

    prim = get_startprim(origin_stage, node, "primpattern")

    all_geo = find_child_prims(prim)
    bad_geo = [{"geometry": "", "attributes": ""}]

    # get all attributes for all geo and add them as a value to the 'attributes' key.
    for geo in all_geo:
        geo["attributes"] = find_prim_attribute_arrays(geo["geometry"])

    for geo in all_geo:
        for key in geo["attributes"]:
            if (
                not compare_attributes(compare_stage, geo["geometry"], key)
                == geo["attributes"][key][0]
            ):
                print(f"The attributes {key} do not match in {geo['geometry']}")


# TODO: Create datastructure to store caught prims and their mismatched attributes.
# TODO: Print to console, or return data to be raised by the HDA with an subnet error node.
