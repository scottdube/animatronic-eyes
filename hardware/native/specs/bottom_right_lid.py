# Bottom Right Lid = the Bottom Left Lid with STL z negated (mircmp max 0.0001 mm), so its spec is that one mirrored
# in the drawing frame (_mirror.py; the rotate op and FRAME turn the other way).
import importlib, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _mirror
importlib.reload(_mirror)   # Fusion's Python keeps modules between runs: never build from a stale copy

_L = _mirror.load("bottom_left_lid")
STL = "../../kit-stl/Bottom Right Lid.stl"
TITLE = "Bottom Right Lid native"
DESCRIPTION = "Native rebuild of the kit's Bottom Right Lid, the Bottom Left Lid mirrored (hardware/native/specs/bottom_right_lid.py)"
FRAME = (_L.FRAME[0], -_L.FRAME[1])
FEATURES = _mirror.mirror(_L.FEATURES, "z")
