# Bo Peep → Willow: first Windows test

Status: **offline validated; not yet tested in Grounded 2**. Target game: PC Game Pass / WinGDK 0.316.9020.0. Buzz V2 and the original reference files are unchanged.

## Install and remove

Close Grounded 2. Extract `BoPeep-Willow-First-Test.zip`. Copy the three files inside `mod` directly into `Augusta\Content\Paks`:

- `zBoPeepTest_P.pak`
- `zBoPeepTest_P.utoc`
- `zBoPeepTest_P.ucas`

Keep all three together. Keep your working Buzz mod installed: this package targets Willow and uses the separate `/Game/_BoPeep0` material namespace. Temporarily move any other Willow replacement outside Paks to avoid competing overrides. Do not overwrite any original game container or Commander101/Buzz files.

Launch, select Willow, and check third-person standing, walking, running, jumping, crouching, punching, sitting and backpack toggling. The menu preview and first-person arms may still show Willow. If anything fails, close the game and remove only the three `zBoPeepTest_P` files. Report launch/crash behavior, pose screenshots, texture orientation and whether original hair remains visible.

## Implemented and independently checked

The supplied Willow extraction contains 14 packages / 10,366,380 decoded bytes. All hashes match; no requested packages or dependencies are missing. The verified gameplay paths are `/Game/_Augusta/Art/Characters/Player_Female01/SK_Female_Teen_01` and `_w_BackPack`. Each has a 192-bone mesh-local skeleton, referencing the shared stock `SK_Male_Teen_01_Skeleton`. Their names/hierarchy agree; rest-transform differences are minute rounding differences. Each original bone table remains byte-exact in its own replacement. Original skeleton, physics and animation assets remain external and are not overridden.

Bo Peep's original 63-bone FBX rig provides semantic weights. The playable body contains 5,028 source vertices / 6,459 triangles, expanded to 5,185 render vertices at UV/tangent seams. A uniform transverse scale preserves the face and body width; segment fitting accommodates Willow's rest-pose limbs. Existing source weights map to native bones. Controlled front, side, sitting and arm/head poses pass finite-coordinate and normalized-weight checks after a fresh Blender reopen. These synthetic poses are not game-animation compatibility tests.

The cape follows torso bones without new cloth simulation. The crook's 391 vertices / 590 triangles, UVs, texture, source weights, transforms and original prop-bone pivot remain separately preserved in the private Blender project. The complete original FBX mesh is also preserved. The crook is excluded from gameplay; no input, gliding, umbrella, movement or collision mechanics are added.

The writer replaces all four cooked LODs of body/backpack with the same low-poly character. Original Willow backpack morph render buffers are replaced with empty morph data; no new facial or backpack morphs are authored. Five stock hair mesh variants use three coincident, identically weighted vertices per LOD to suppress original Willow hair. Their original 16-bone tables remain intact. Character-select and first-person mesh packages are not included.

The native CUE4Parse reader independently parses all 28 LODs. Final positions, triangle indices, section palettes, weights, UVs, colors and reference skeletons match intended output. Material slot zero resolves through its actual Zen package-index/public-export-hash reference to the private Bo Peep material. That material's Albedo/Normal/RMA/SSSMask parameters resolve to four private textures; the original cached character shader payload remains exact. The source 512² texture is upscaled to a 4096² sheet with explicit Blender-to-Unreal V reversal. All 50 mip payloads match fresh CUE reads. Independent BC3 decoding has RGB mean absolute error 1.542/255; the BC5 normal decodes to constant RG128 at every mip, avoiding the earlier striped-normal encoding problem.

The 12-package / 17-chunk IoStore verifies, unpacks to exact staged chunk hashes, and converts back to legacy exports/bulk with exact native payloads. No Max/Buzz paths, USkeleton or physics assets are bundled. Runtime compatibility still requires the Windows test.

## Expected visual compromises

One opaque material supplies simplified shared lighting for face, eyes, cloth and hair. No facial animation or cloth simulation is added. The cape may intersect chairs/legs and the body may need minor pose/foot/hand refinements after the first test. Four identical LODs trade distant optimization for a simple validated first build. Original voice, portraits, menu mesh and first-person arms may remain Willow. Bo Peep's source archive has no bundled license/readme/exact listing URL; it is recorded as the user-provided Sketchfab source, without invented attribution or redistribution rights.

## Reproduce from preserved workspace inputs

Run from `/workspace/Grounded2Skins`, with Blender 4.3.2, retoc 0.1.5, pinned CUE4Parse 1.2.2, .NET 10.0.402, NumPy, Pillow, cityhash, ispc_texcomp and texture2ddecoder. Existing cloud setup preserves the pinned tools. Every script requires a new output directory; do not rerun against an existing output.

1. `rig_bopeep_blender.py`: open `body-and-crook-v2/BoPeep-source-body-and-crook.blend`; arguments `willow-stock/rig-reference.json NEW_RIG`. Produces `BoPeep-Willow-skinned.blend`, expected arrays and semantic-mapping report.
2. Fresh reopen: `validate_render_bopeep.py NEW_REVIEW`; `validate_bopeep_source.py` against a new copy of `prop-preservation.json`. No saved source scene changes.
3. `export_bopeep_geometry.py`: open the skinned blend; arguments `REFERENCE RIG_REPORT NEW_GEOMETRY --skinned`. Explicit V reversal and tangent-handedness conversion; no source texture modification.
4. `native_buffers.py GEOMETRY_NPZ REFERENCE NEW_BUFFERS` encodes section palettes, buffers and exact-sum UNORM8 weights. The original 230-bone Buzz defaults remain covered by the four CUE round-trip and ten rejection checks in `test_native_buffers.py`.
5. `write_willow_lods.py STOCK STOCK_NATIVE_PROFILES BUFFERS REFERENCE NEW_COOKED` requires the actual hashed Willow profiles from `native-lod-probe`; replaces four LODs, bounds, Zen mesh-export sizes and the zero-size Nanite bulk offset.
6. Upscale `source/textures/bo_peep_d.png` to 4096² RGBA with Pillow Lanczos. Use `write_buzz_atlas_textures.py` with the existing original Commander raw/templates and metadata, writing only a new stage. Then `clone_bopeep_material_templates.py TEXTURED_RAW STOCK_MI NEW_PRIVATE_TEMPLATES` creates the private `_BoPeep0` / `_Bop_` copies. This intermediate retains the reference package layout; the next step selects only Bo Peep's assets.
7. `assemble_bopeep_zen.py COOKED STOCK PROFILES PRIVATE_TEMPLATES NEW_RAW` selects seven Willow meshes and five private assets, relocates the variable-length imported-package name batches/public hashes and rebuilds the v5 package store.
8. `repackage_iostore.py RAW ORIGINAL_EMPTY_PAK NEW_PACKAGE --mod-name zBoPeepTest_P` writes new IDs, block offsets/hashes, verifies and unpacks. `readback_bopeep_package.py NEW_CHECK PACKAGE` independently parses the final assets and converts via retoc using the preserved global container.
9. Add `native-buffers` and `textured` symlinks under the check directory to the corresponding new stages, then `validate_bopeep_final.py CHECK STOCK_REFERENCE_SKELETONS NEW_REPORT`. `render_cooked_bopeep_preview.py CHECK` renders the actual decoded mesh/texture read-back, separate from Blender authoring previews.

Current private stage root: `/workspace/mod-work/bopeep-stage`. Final authoring: `rig-v2`; final geometry/buffers/cooked/raw/package/check stages: `geometry-v3`, `buffers-v3`, `cooked-v3`, `raw-v3`, `package-v3`, `final-check-v3`. Original source, extraction, Buzz outputs and earlier diagnostics remain preserved.
