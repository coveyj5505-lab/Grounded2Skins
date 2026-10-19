# Jessie preparation — Hoops replacement

User requested Jessie preparation while testing Bo Peep. Buzz is accepted complete; Bo Peep's first test awaits user results. Preserve both. Jessie will use separate `zJessieTest_P` files and `/Game/_Jessie0` material/texture paths; no existing character paths except verified Hoops targets will be overridden.

## Supplied model already inspected

`jessie.zip` (user upload, SHA256 `4cb7bbb28ff812c03c483ec2331b3c9e5f0e87129515e4cb4a96b3a0958700b3`) contains `source/Jessie.fbx` and three PNGs: 2048² diffuse, 512² specular and 512² normal. No license/readme or exact listing URL is bundled. A preliminary Sketchfab search is not provenance for this actual archive; do not infer the source/uploader from a similar model. No additional model download is needed.

Blender 4.3.2 imports three mesh objects (3,449 + 1,288 + 146 vertices; 6,008 + 2,493 + 256 triangles), totaling **4,883 vertices / 8,757 triangles**. A **163-bone source rig**, including hat and ponytail bones, is present; all vertices have weights and there are no animation actions. Source rest pose is already approximately A-pose. The diffuse sheet is fully opaque. Preserve source proportions, hat and braid rather than stretching facial landmarks to game anatomy.

The FBX's imported material slots have no texture nodes. A reversible working copy packs all three PNGs and provisionally connects the supplied diffuse sheet. Rendered front/back/side previews confirm recognizable hat, shirt, belt, cow-print chaps and boots. The separate 146-vertex eye mesh uses a full-sheet UV layout and maps incorrectly to the body diffuse. Its original material has no image binding and no dedicated eye texture is supplied. Resolve an isolated eye material/atlas region before gameplay packaging; the user's archive need not be replaced. Normal/specular maps are packed and preserved but their channel semantics are not assumed. Use the proven flat BC5/matte material fallback initially if necessary.

Private stage: `/workspace/mod-work/jessie-stage`. Imported original working scene: `inspection/Jessie-source-inspection.blend`. Packed provisional-texture scene: `textured-source/Jessie-source-textured.blend`; front/back/side previews and `source-preparation.json` alongside it. Fresh-process fingerprints compare original import and packed scene geometry, triangle order, UVs, weights, object matrices and source bone rest matrices exactly; texture/material changes do not alter the source rig.

## Technical reference actually extracted

The supplied SuperEvie trio is a **third-party custom Hoops mod**, not stock Grounded 2. All 33 chunks / 21 packages unpack successfully. Its gameplay targets are:

- `/Game/_Augusta/Art/Characters/Player_Female02/SK_Female_Teen_02`
- `/Game/_Augusta/Art/Characters/Player_Female02/SK_Female_Teen_02_w_BackPack`

Both have identical 230-bone mesh-local tables. The native CUE reader successfully reads 27,047 vertices / 45,833 triangles / ten sections / one LOD with cloth data and normalized UNORM8 weights. Four hair variants have 12 bones. This is useful package-layout evidence, **not proof of stock Hoops rest transforms or physics equality**. Do not force either Willow's 192 or SuperEvie's 230 bones onto Jessie without the stock comparison.

Private extracted reference is `reference-raw`; `reference-metadata.json`, `reference-skeletons.json`, body/backpack readbacks and `preparation-report.json` preserve actual findings. Original reference files are unchanged. Existing Buzz/Bo Peep geometry encoder, four-LOD serializer, Zen import relocation, private material cloning and IoStore validation can be reused after profiling stock Hoops. No arbitrary UE editor cooking is proposed.

## One remaining input before native binding

Run `Hoops-Compatibility-Extractor.zip` using the same Windows retoc 0.1.5 / Python 3.11+ setup that worked for Willow. Extract it, launch `Start-Extraction.cmd`, choose retoc.exe and original `Augusta-WinGDK.utoc` (with adjacent UCAS). Upload the Desktop `Grounded2-Hoops-[timestamp].zip`.

The helper discovers actual indexed meshes under `Player_Female02`, reads their real skeleton/physics imports and extracts only selected packages. No full-game copy, texture dump, injection, game installation edits or installed mod overrides. It caps output at 48 packages / 128 MiB decoded. It returns available chunks and a report even when dependencies are missing; use those rather than blindly repeating extraction.

Actual control runs: SuperEvie yields seven selected packages / 3,697,469 decoded bytes with matching known raw hashes, no header errors, unchanged source size/mtime, and correctly reports its two unavailable original skeleton dependencies. Commander101 yields zero Hoops packages. These are tool controls, not stock Hoops evidence. Windows dialog UI is inherited from the user's successful launcher and is not executable in this Linux environment.

Next: verify uploaded stock Hoops hashes/bone hierarchy/rest pose/LOD layout; map the source's anatomical weights (face/hat to head, fingers individually, braid conservatively), preserve uniform head/body width; controlled pose checks and fresh reopen; isolated textured package and independent read-back. No Jessie gameplay ZIP or runtime compatibility is claimed yet.
