from pxr import Sdf, Usd

node = hou.pwd()
stage = node.editableStage()


def get_version_int(v: str):
    version_int = int(v[1:].zfill(3))
    return version_int


# HDA inputs.
input_prim = node.parm("primpattern").eval()
subtract_from_version = node.parm("subtractversion").eval()

# Resolve Usd.Prim object.
prim = stage.GetPrimAtPath(input_prim)

# Gather child Usd.Prims with child payloads.
iterator = iter(Usd.PrimRange(prim))
prims_with_payloads = set()

for prim in iterator:
    if (
        Usd.ModelAPI(prim).GetKind() == "component"
        or Usd.ModelAPI(prim).GetKind() == "prop"
        or Usd.ModelAPI(prim).GetKind() == "setprop"
    ):
        prims_with_payloads.add(prim)

# Set all Usd.Prims with payloads versions.
for prim in prims_with_payloads:
    # Find variant set 'version'.
    variant_sets = prim.GetVariantSets()
    version_set = variant_sets.GetVariantSet("versions")

    # Get highest 'version' of given variant name list.
    try:
        highest_version = max(version_set.GetVariantNames(), key=get_version_int)
    except ValueError as e:
        print(f'An error occurred: {e}. Variant set "versions" not found.')
        raise

    if highest_version is not None:
        # Parse version number.
        new_version_int = get_version_int(highest_version) - subtract_from_version
        new_version_str = "v" + str(new_version_int).zfill(3)

        # Set the new version.
        if new_version_int > 0:
            version_set.SetVariantSelection(new_version_str)
        elif new_version_int <= 0:
            version_set.SetVariantSelection("v001")
