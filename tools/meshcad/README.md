# meshcad: decode an STL into dimensions for a native Fusion rebuild

Run with `uv run --no-project --with numpy --with matplotlib python -I <script> <stl> tools/meshcad [out]`.
`stlmesh.py` has the loader, plane sections, vertical ray hits and a circle fit. The `a*.py` scripts are
the passes used on the Eye Adaptor (2026-10-13): sections in z (a2), planar faces with extents (a3),
vertical sections (a4), top-surface height map (a5), circle fits (a6), outline vertices (a7), shaded views
(render). Tessellated arcs put their VERTICES on the true circle, so fit vertices, not raster samples.
