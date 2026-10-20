# Woody boots and ring: separate V2 test

This Woody-only update is independent of the frozen Buzz/Bo Peep v0.3. No Lua or other character files are bundled. It preserves the working Pete replacement paths, textures, proportions, 188-bone body references and first-person head/body section split. Windows validation remains pending.

## Actual defects and changes

The preserved source FBX has cowboy boot pull-tabs, not shoelaces. The inner tabs crossed the center plane even at rest, and the previous per-vertex X-side fitting assigned 72 of their vertices to the opposite lower-leg bone. Comparison reproduced the original fit to within 1.49e-8m, establishing the cause before editing. Use original anatomical source weights to keep each complete tab on its own leg, then tuck each tab about3.33cm toward its own cuff. Original tab shape/topology/UVs remain; nothing is deleted. Boot bodies, soles and spurs retain their original fit.

The original source ring is circular (10.8182cm X /10.8194cm Z). Torso scaling plus nonlinear vertical fitting stretched it to14.6045cm /28.0265cm. Its existing rigid spine3 weight was already correct. A uniform1.35 similarity on the ring and mounting piece restores14.6045cm /14.6062cm, keeping their mutual attachment intact. No replacement skeleton or new accessory system is needed.

Only519 of32379 source vertices move; only72 change bone assignments. All original triangle topology, UVs, material assignments, head/body classification and other weights remain. Main and backpack variants have32601 render vertices,54801 triangles, four independently read LODs each. The other19 package chunks, including textures/materials and menu meshes, are byte-identical to the accepted first-person baseline. Character-selection preview retains the previous geometry, so judge this update on the actual playable Pete/Woody.

## Install and rollback

Close Grounded2. Move the three old zWoodyFP_P files outside Augusta/Content/Paks. If an older zWoodyTest_P trio is also installed, move that outside too. Copy the new zWoodyPolishV2_P.pak/.utoc/.ucas from the ZIP's Paks folder into Augusta/Content/Paks. Keep Buzz, Bo Peep, Jessie, v0.3 runtime folders and accessory packages unchanged. There are no installers or mods.txt changes.

Rollback: close the game, remove only zWoodyPolishV2_P's three files and restore your old Woody trio. Original release archives remain untouched.

When convenient, test standing, running, sitting, crouching and both camera views. Boots should no longer join across the feet, and the back ring should remain circular. No new test is required before continued independent development. This does not claim perfect boot contact in every game animation.

## Validation and reproduction

Fresh Blender standing/running/sitting FK previews pass: finite positions, single-leg boot ownership and rigid ring pairwise distances within1e-6m. These are synthetic poses, not extracted gameplay clips.

Fresh CUE4Parse package read-back checks intended positions, indices, quantized weights, global joints, UVs, colors and packed normal/tangent streams; original materials/reference-bone bytes and native tails are preserved. Actual packaged triangle corners match freshly reopened Blender within7.63e-8m. Head/body material indices resolve to the same existing private Woody atlas through actual public export hashes; all50 fresh texture mips match the original release. All17 Zen export payloads independently round-trip to legacy exactly. Container verification and re-unpacking match every staged chunk.

Accepted private stages: /workspace/mod-work/woody-polish-next/authoring-v2 -> export-v2 -> build-v2 -> package-v2 -> check-v2 -> Woody-Polish-Cooked-Verified.blend -> cooked-previews-v2. Reproduce with refine_woody_boots_ring.py, existing export_woody_geometry.py, build_woody_polish.py (existing native encoder and Pete writer), existing repackage_iostore.py --mod-name zWoodyPolishV2_P, existing readback_woody_package.py, existing validate_measured_mesh_rewrite.py, verify_woody_polish_cooked.py, preview_woody_polish.py and package_woody_polish.py. Inputs and outputs are separate; writers reject existing output paths.
