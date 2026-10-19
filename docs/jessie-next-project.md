# Jessie preparation — Hoops replacement

User requested Jessie preparation while testing Bo Peep. Buzz is accepted complete; Bo Peep's user test confirms walking, running, jumping and crouching, with hand/cape issues recorded separately. Preserve both. Jessie will use separate `zJessieTest_P` files and `/Game/_Jessie0` material/texture paths; no existing character paths except verified Hoops targets will be overridden.

## Supplied model already inspected

`jessie.zip` (user upload, SHA256 `4cb7bbb28ff812c03c483ec2331b3c9e5f0e87129515e4cb4a96b3a0958700b3`) contains `source/Jessie.fbx` and three PNGs: 2048² diffuse, 512² specular and 512² normal. No license/readme or exact listing URL is bundled. A preliminary Sketchfab search is not provenance for this actual archive; do not infer the source/uploader from a similar model. No additional model download is needed.

Blender 4.3.2 imports three mesh objects (3,449 + 1,288 + 146 vertices; 6,008 + 2,493 + 256 triangles), totaling **4,883 vertices / 8,757 triangles**. A **163-bone source rig**, including hat and ponytail bones, is present; all vertices have weights and there are no animation actions. Source rest pose is already approximately A-pose. The diffuse sheet is fully opaque. Preserve source proportions, hat and braid rather than stretching facial landmarks to game anatomy.

The FBX's imported material slots have no texture nodes. A reversible working copy packs all three PNGs and provisionally connects the supplied diffuse sheet. Rendered front/back/side previews confirm recognizable hat, shirt, belt, cow-print chaps and boots. The separate 146-vertex eye mesh uses a full-sheet UV layout and maps incorrectly to the body diffuse. Its original material has no image binding and no dedicated eye texture is supplied. Resolve an isolated eye material/atlas region before gameplay packaging; the user's archive need not be replaced. Normal/specular maps are packed and preserved but their channel semantics are not assumed. Use the proven flat BC5/matte material fallback initially if necessary.

Private stage: `/workspace/mod-work/jessie-stage`. Imported original working scene: `inspection/Jessie-source-inspection.blend`. Packed provisional-texture scene: `textured-source-v2/Jessie-source-textured.blend`; front/back/side previews and `source-preparation.json` alongside it. Fresh-process fingerprints compare original import and packed scene geometry, triangle order, UVs, weights, object matrices and source bone rest matrices exactly; texture/material changes do not alter the source rig.

## Technical reference actually extracted

The supplied SuperEvie trio is a **third-party custom Hoops mod**, not stock Grounded 2. All 33 chunks / 21 packages unpack successfully. Its gameplay targets are:

- `/Game/_Augusta/Art/Characters/Player_Female02/SK_Female_Teen_02`
- `/Game/_Augusta/Art/Characters/Player_Female02/SK_Female_Teen_02_w_BackPack`

Both have identical 230-bone mesh-local tables. The native CUE reader successfully reads 27,047 vertices / 45,833 triangles / ten sections / one LOD with cloth data and normalized UNORM8 weights. Four hair variants have 12 bones. This is useful package-layout evidence, **not proof of stock Hoops rest transforms or physics equality**. Do not force either Willow's 192 or SuperEvie's 230 bones onto Jessie without the stock comparison.

Private extracted reference is `reference-raw`; `reference-metadata.json`, `reference-skeletons.json`, body/backpack readbacks and `preparation-report.json` preserve actual findings. Original reference files are unchanged. Existing Buzz/Bo Peep geometry encoder, four-LOD serializer, Zen import relocation, private material cloning and IoStore validation can be reused after profiling stock Hoops. No arbitrary UE editor cooking is proposed.

## Stock Hoops received and verified

The user supplied `Grounded2-Hoops-20261018-194644-471.zip`: **13 packages / 10,068,423 decoded bytes**, all chunk hashes and sizes valid, no missing targets, errors or header warnings; report records original size/mtime unchanged. The ZIP uses Windows backslashes: normalize separators safely rather than asking for another extraction. `inspect_character_extraction.py` reproduces the normalization, verification, metadata and skeleton reads exactly.

Stock gameplay body/backpack each have **189 mesh-local bones and four cooked LODs**, unlike the third-party SuperEvie 230-bone/one-LOD layout. Shared original game skeleton has 195 bones; original stock physics is supplied. Stock hair has four variants with 12 bones and four LODs. Main stock LOD0 has 18,841 vertices / 27,820 triangles; backpack has 24,502 vertices / 36,388 triangles (consult actual native readback for authoritative counts). CUE independently parses both gameplay meshes and all four hair variants. Do not request any further stock extraction or force SuperEvie's custom bone table onto Jessie.

Use `/workspace/mod-work/jessie-stage/hoops-stock-normalized` (normalized verified data), `stock-native-profiles.json`, and `stock-vs-superevie.json`. The reference-mod comparison has extra/missing bones, reordering and local-pose differences; the stock table is authoritative. No original physics, USkeleton or animation override is planned. Do not reuse custom cloth data.

## Initial native binding prepared

`rig_jessie_blender.py` preserves the supplied source armature/meshes and creates a new stock 189-bone rig with source anatomical skin weights mapped by name/ancestry. It maps all five Biped finger chains separately; terminal digit segments inherit a fitted frame rather than identity. Facial, hat and braid helpers use a common head transform. Source mesh topology/UVs remain unchanged. Unweighted FBX root/helper bones are explicitly excluded from deformation mapping. All three PNGs have persistent packed-image users so unused normal/specular images survive repeated saves.

Current private scene: `rig-v5/Jessie-Hoops-skinned.blend`; fresh-process `rig-v5-review/validation.json` verifies all 4,883 vertices are weighted/normalized, native 189 bone order, original UV/topology, three packed images and finite synthetic sitting/finger-curl poses. These tests do not prove good appearance or game-animation compatibility. Front/side/sitting previews were rendered; front/sitting were inspected. The initial fit still has an elongated neck/shoulder silhouette, and the eye material remains provisional. Do not package or label this initial fit finished. Refine those before an installable Jessie test, preserving all source assets and the verified stock skeleton.

No additional user input is required for the next fitting/material work. No Jessie gameplay ZIP exists yet. Existing Buzz and the verified Bo Peep test remain unchanged. The Hoops helper remains available for reproducibility but the user's data is already complete.

## First installable test completed

The subsequent `rig-v6` adjusts the neck fit; `gameplay-v1` combines preserved parts with a body/temporary-green-eye atlas. Full four-LOD writing, private materials, Zen relocation, IoStore verification and independent native/texture readbacks are complete. The new `Jessie-Hoops-First-Test.zip` / `zJessieTest_P` is separate from Buzz and Bo Peep and awaits the user's Windows test. [Installation, compromises and reproduction](jessie-first-test.md) supersede earlier unfinished-stage notes.

## Jessie V2 correction

User confirmed V1 runtime loading/rendering but reported major limb, chaps and torso deformation. A focused V2 corrects twist-role mapping and coherent clothing fitting while preserving the accepted head/atlas and existing releases. See [V2 diagnosis, validation and installation](jessie-v2-test.md). V2 remains untested in Windows until user feedback.
