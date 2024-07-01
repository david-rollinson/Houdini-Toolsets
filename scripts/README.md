# Scripts: Info

[check_prim_extents.py](https://github.com/david-rollinson/Houdini-Toolsets/blob/main/scripts/check_prim_extents.py) takes a Usd.Prim as input, finds all child prims with child payloads. It then recalculates the extentHint attribute, checking it against the prims' current extentHint. This is to be used to check bounding box accuracy across prims. 