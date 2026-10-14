# Top Right Lid: the Top Left Lid with STL z negated (vertex sets identical to 0.0000 mm, 2026-10-13). In the
# left lid's drawing frame that is z' -> -z', and the frame turn reverses: STL = Mz Rx(-20) q = Rx(+20) Mz q.
# Every dimension is the left lid's (specs/top_left_lid.py); edit there and both follow.
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _mirror

_L = _mirror.load("top_left_lid")
STL = "../../kit-stl/Top Right Lid.stl"
TITLE = "Top Right Lid native"
DESCRIPTION = "Native rebuild of the kit's Top Right Lid, the Top Left Lid mirrored (hardware/native/specs/top_right_lid.py)"
FRAME = (_L.FRAME[0], -_L.FRAME[1])
FEATURES = _mirror.mirror(_L.FEATURES, "z")
