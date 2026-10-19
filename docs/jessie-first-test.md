# Jessie replaces Hoops — first gameplay test

**V1 user test confirms loading, animation and rendering, with major body deformation.** See `jessie-v1-windows-test.json` and `jessie-v2-test.md`. V1 ZIP remains the unchanged fallback. Target: Grounded 2 PC Game Pass / WinGDK build 0.316.9020.0.

## Install

1. Close Grounded 2 and extract `Jessie-Hoops-First-Test.zip`.
2. If SuperEvie or another Hoops replacement is installed, move its files completely outside `Augusta\Content\Paks`. For SuperEvie, move all three `zSuperEvie_P.pak`, `.utoc`, `.ucas` files together. Do not delete or overwrite them.
3. Copy the three files inside this ZIP's `mod` folder directly into `Augusta\Content\Paks`:
   - `zJessieTest_P.pak`
   - `zJessieTest_P.utoc`
   - `zJessieTest_P.ucas`
4. Leave your working Buzz and Bo Peep mods installed. Select **Hoops** to play Jessie.

To remove: close the game and remove only those three `zJessieTest_P` files. Restore your previous Hoops mod if desired. Do not overwrite any original Augusta game container.

Test launch, third-person standing, walking, running, jumping, crouching, punching, sitting, equipment grips and backpack toggling. Report crashes, missing textures, original hair showing, hand/collar/shoulder deformation and whether both backpack states show Jessie. Menu preview, first-person arms, voice and portraits may remain Hoops.

## What this build contains

Jessie's supplied FBX geometry, hat, braid, face, outfit, boots and diffuse texture; 4,883 authoring vertices / 8,757 triangles, expanded to 6,844 render vertices at UV/tangent seams. She is bound to the **actual stock Hoops 189-bone mesh skeleton**, preserving each source body's original bone table, original animation and physics references. SuperEvie's third-party 230-bone custom skeleton is not used as the authoritative bind pose.

The native writer replaces four LODs of both body/backpack variants with the same low-poly Jessie geometry. Four original hair variants become invisible coincident triangles, retaining their own 12-bone skeletons/four LODs. No USkeleton, physics asset, character Blueprint, movement, combat or collision capsule override is included. No custom animations or new controls.

One private material and four private textures live under `/Game/_Jessie0`; the folder `Player_Male01` inside that *private* namespace is only the borrowed material-template location, not a Max override. Jessie/Bo Peep/Buzz override paths and chunk IDs are disjoint. Other original unused Hoops material imports remain external; the actual rendered section points to Jessie's private material.

## Visual compromises

The supplied archive has no separate eye texture or valid FBX texture bindings. This test uses a documented **temporary procedural green-eye texture**, not a recovered original eye texture. The original eye geometry/UVs and all source assets remain preserved in the private source scenes. The diffuse body sheet and temporary eye sheet are combined into one atlas.

A flat BC5 normal, matte RMA and black subsurface mask provide simple shared shading for skin, eyes, hair and clothing. The original supplied normal/specular PNGs are preserved and packed for later material work. Hat and braid follow the head without new secondary physics. The initial neck fit was adjusted to stock `neck3_JNT`; collar, angular shoulders, hands, sitting knees and equipment interactions may still need refinement after gameplay testing. No facial expression system is added. Four identical LODs favor a simple first test over distant optimization.

## Offline validation actually completed

The uploaded original Hoops extraction has 13 packages / 10,068,423 decoded bytes, all reported hashes and sizes valid, no missing dependencies. CUE4Parse reads all four native LODs of both gameplay meshes and all four hair variants. The final 11-package / 16-chunk IoStore verifies and unpacks to byte-exact staged hashes; legacy export/bulk conversion is exact. Native mesh positions, indices, section palettes, weights, material assignments, UVs, colors and original reference skeletons match intended output. All weights quantize to exact UNORM8 total 255.

The actual Zen material reference resolves through package index and public-export hash to the private MI, whose Albedo/Normal/RMA/SSSMask parameters resolve to Jessie's private textures. Original MM_Character cached material payload is retained. Independent CUE texture readback checks 50 mip levels. Independent BC3 decoding has RGB mean absolute error about 1.536/255; all flat BC5 normal mips decode to RG128, avoiding the earlier striped normal-map bug. Tangent and normal component errors are below 0.004 and tangent signs match. Atlas UVs have explicit Blender-to-Unreal V reversal and native half-float readback checks. Actual decoded cooked front/side previews are included.

A fresh Blender reopen checks geometry/UV arrays, normalized weights, four packed images and finite standing, side, synthetic sitting and finger-curl poses. These are controlled offline tests, not proof of real game animation or crash-free runtime compatibility. Only your Windows test can establish that.

## Reproduction and preserved stages

Working root: `/workspace/mod-work/jessie-stage`. Final native rig: `rig-v6/Jessie-Hoops-skinned.blend`; combined atlas scene: `gameplay-v1/Jessie-Hoops-gameplay.blend`. Original source/imports and earlier diagnostics remain unchanged.

Scripts in `pipeline`, each using a **new output directory**:

1. `inspect_character_extraction.py ZIP NEW_STOCK SK_Female_Teen_02` safely normalizes Windows ZIP separators, verifies chunk hashes and reads native skeletons. Actual Hoops metadata/profiles remain under `hoops-stock-normalized` and `stock-native-profiles.json`.
2. `rig_jessie_blender.py STOCK_RIG_REFERENCE NEW_RIG`, run against `textured-source-v2/Jessie-source-textured.blend`: map original Biped weights to stock Hoops, keep facial/hat/braid head transform and source originals.
3. `create_jessie_atlas.py ORIGINAL_DIFFUSE NEW_ATLAS`; then `prepare_jessie_gameplay.py ATLAS NEW_GAMEPLAY`, run against the native rig. A fresh `validate_jessie_gameplay.py EXPECTED_NPZ NEW_REVIEW` checks and renders the combined scene.
4. `export_jessie_geometry.py STOCK_RIG_REFERENCE RIG_REPORT NEW_GEOMETRY --skinned`, run against the gameplay scene; `native_buffers.py GEOMETRY_NPZ STOCK_RIG_REFERENCE NEW_BUFFERS`; `write_hoops_lods.py STOCK PROFILES BUFFERS STOCK_RIG_REFERENCE NEW_COOKED`.
5. Use `write_buzz_atlas_textures.py ORIGINAL_COMMANDER_RAW ORIGINAL_METADATA JESSIE_ATLAS NEW_TEXTURE_STAGE`, then `clone_jessie_material_templates.py TEXTURED_RAW ORIGINAL_STOCK_MAX_MI NEW_PRIVATE_TEMPLATES`. These write new private template copies, not original game/Buzz/Bo Peep assets.
6. `assemble_jessie_zen.py COOKED STOCK PROFILES PRIVATE_TEMPLATES NEW_RAW`; `repackage_iostore.py RAW ORIGINAL_EMPTY_PAK NEW_PACKAGE --mod-name zJessieTest_P`.
7. `readback_jessie_package.py NEW_CHECK PACKAGE`; add `native-buffers`/`textured` symlinks to their corresponding stages; `validate_jessie_final.py CHECK STOCK_REFERENCE_SKELETONS NEW_REPORT`; `render_cooked_jessie_preview.py CHECK`.

Current stages: `atlas-v1`, `gameplay-v1`, `geometry-v1`, `buffers-v1`, `cooked-v1`, `textures-v1`, `private-templates-v1`, `raw-v2`, `package-v2`, `final-check-v2`, `frames-v1`. `validation-report-v2.json` is the final corrected report. Keep earlier stages as diagnostics, not distribution files.

Tools reused: Blender 4.3.2; pinned retoc 0.1.5; CUE4Parse 1.2.2 / GAME_Grounded2 UE5.6; .NET 10.0.402; NumPy/Pillow/cityhash/ispc_texcomp/texture2ddecoder. No arbitrary Unreal editor cook is assumed compatible. The uploaded source archive has no bundled license or exact listing URL; no attribution or source redistribution permission is invented. Raw FBX/PNGs and private Blender scenes are not in this gameplay ZIP.
