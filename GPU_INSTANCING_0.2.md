# PlantView Studio 0.2 — GPU instancing (experimental)

- Identical translated PolyData with identical vertex order, topology and color are fed to `vtkGlyph3DMapper` as one actor per group (three or more occurrences).
- Groups preserve entity names in the tree and model-level hide/show, but **individual glyph selection is not implemented**. Objects with different colors are not combined.
- Rotated, mirrored, differently tessellated or nonidentical geometry is NOT deduplicated.
- CPU still performs DWG parsing, ACIS decoding and CAD triangulation. GPU performs OpenGL rendering and glyph instancing. Calling the entire model pipeline GPU-only is inaccurate.
- Tests run here: Python syntax compilation. The Windows build, GPU availability, visual accuracy, real DWG solid support, hardware FPS/memory, and rendering of grouped actors have **not** been validated.

## Windows GPU performance validation

1. Install dependencies from `requirements-lock.txt`, build native DWG reader from `dwg-reader/` as documented in LEIA-ME.md.
2. Open the same `pvproj` in version 0.1 and this version, preferably containing repeated pipes, flanges or equipment.
3. Select 'Diagnóstico GPU'; verify hardware vendor/renderer is the actual card rather than Microsoft Basic Render Driver / software rasterization.
4. Record scene triangles, load time (wall clock), GPU VRAM, FPS while moving the camera for 60 seconds at identical view/resolution, and compare.
5. Verify coordinates, ByLayer/ByBlock colors, F5 reload, camera, visibility and all repeated objects from three independent DWGs.
6. A rollback test should verify no missing geometry and no unexpectedly merged different parts; restore 0.1 if a CAD mismatch appears.

No FPS improvement percentage is claimed without a physical GPU test.
