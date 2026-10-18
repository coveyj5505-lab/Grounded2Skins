# Atlas staging checkpoint — not a finalized gameplay mod

The user approved a temporary single-material atlas test, then requested a
stock-Max compatibility assessment before finalizing it. That gate takes priority;
[the current assessment](commander-stock-max-assessment.md) identifies original
packages needed for a truthful comparison. No new gameplay ZIP is finalized.

Preserved private stage: `/workspace/mod-work/buzz-test-stage`.

- `source-images`: all eight original packed images extracted without modification,
  material-image links and original hashes recorded. All images are opaque.
- `atlas`: 4096x4096 repeat-aware atlas, per-material affine UV remap and original
  source-material IDs retained as metadata. Eight source images remain untouched.
  Native V orientation and tangent handedness are explicitly adjusted.
- `native-buffers` / `cooked`: new atlas mesh buffers and complete LODs, still using
  the recovered Commander101 reference skeleton. All atlas faces select original
  material slot0, `MI_Character_Male01_Max_Apparel01`; this is temporary flattening
  of the original eight Blender material slots, not creation of eight Unreal MIs.
- `textured`: size-preserving replacement of four Max-specific texture mip chains,
  eight export/bulk chunks. Color DXT5 atlas, neutral BC5 normals, temporary matte
  DXT1 RMA, black DXT1 subsurface mask. Original formats, dimensions, mip records,
  offsets/flags and all non-pixel header bytes are preserved. These replacements
  exist only in a new mod staging copy, not in game/original mod files.
- `original-color-readback-v2`: CUE4Parse independently reads the original 4096px
  base-color texture and all13mips. Full Package construction requested missing
  property mappings; the successful reader instead parses actual serialized header
  and data-resource tables, supplies that context to unchanged native texture
  readers, and never pretends to deserialize UObject properties. It does not alter
  third-party CUE4Parse source or fabricate a property schema.

Dependencies: `pipeline/requirements-materials.txt`, installed into
`/workspace/toolchains/material-python`. Commands need that directory on
`PYTHONPATH`. The texture probe builds with the same pinned CUE4Parse/.NET profile
as the native LOD probe. Source color-channel calibration checked independent BC
encoder/decoder BGRA conventions. Modified mip chains, final UV/color previews,
material sampler bindings, references and final container roundtrip still need
independent validation after the compatibility gate. No runtime claim is made.

The original game material instance is external to the uploaded mod. Replacing
only geometry's material slot is insufficient; its actual texture dependency must
be checked. The stock extractor includes that MI. A future private cloned MI and
private texture paths may offer stronger isolation than overriding shared Max
texture paths, once its real parent/parameter references are available. No full
original-game reverse-reference graph is present, so exhaustive claims about
unrelated uses of Max-specific textures are not currently justified.

Source-only reproduction after the gate, using new output directories:

```bash
blender -b /workspace/mod-work/rig-stage/skinned-stowed-v9/Buzz-Grounded2-skinned.blend --python-exit-code 1 --python pipeline/export_buzz_material_images.py -- /path/to/NEW-source-images
python pipeline/build_buzz_atlas.py /workspace/mod-work/rig-stage/skinned-export-v9/Buzz-geometry-SKINNED.npz /path/to/NEW-source-images /workspace/mod-work/global-stage/reports/reference-skeletons.json /path/to/NEW-atlas
python pipeline/native_buffers.py /path/to/NEW-atlas/Buzz-atlas-SKINNED.npz /workspace/mod-work/global-stage/reports/reference-skeletons.json /path/to/NEW-buffers
python pipeline/write_resized_lod.py /workspace/mod-work/retoc-raw /path/to/NEW-buffers /workspace/mod-work/global-stage/reports/reference-skeletons.json /path/to/NEW-cooked
PYTHONPATH=/workspace/toolchains/material-python python pipeline/write_buzz_atlas_textures.py /path/to/NEW-cooked/raw /workspace/mod-work/reports/commander-packages.json /path/to/NEW-atlas/Buzz-basecolor-atlas.png /path/to/NEW-textured
```

Preserve the current 230-bone rig, original extended wings, eight textures, source
OBJ, Commander originals and previous Max test release. Stock comparison may
justify a controlled rebind or targeted physics/material correction; it does not
justify discarding the mesh encoder or proven packaging pipeline.
