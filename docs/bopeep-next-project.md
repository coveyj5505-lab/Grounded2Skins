# Bo Peep replaces Willow

User marked Buzz complete and moved priority to Bo Peep, then Woody/Pete, then Jessie/Hoops. Working Buzz V1/V2 files and pipeline remain unchanged. Reuse the proven native encoder/LOD writer, flat-BC5 fix, private materials, IoStore pack/readback, Blender fitting/weights and source-proportion lessons. No other characters or optional polish before Bo Peep's first gameplay test.

## Supplied source inspected

User supplied `bo-peep-toy-story.zip` from Sketchfab; archive SHA25641bd13601371d3cb5c92c84b2f69309e9d2fc8c65cae1e0b9a30cbed49ed4b49. It contains `source/bo_peep.fbx`422,892bytes and `textures/bo_peep_d.png`130,641bytes. No license/readme or exact source URL is bundled; do not attribute it to a searched listing just because its title/polycount resembles this archive. The FBX itself was imported and rendered, not inferred from a listing thumbnail.

Blender4.3.2 imports5,419vertices/7,049triangles, one used material and a63-bone source rig. All5,419vertices have weights;43deform groups are present, with no animation actions. One opaque512x512RGBA texture (alpha255 everywhere) is referenced by two Blender image nodes and packed successfully after resolving the actual archive texture path. Body proportions have not been changed. Source object transforms include FBX rotation/scale; do not ignore those or fit each axis independently.

The actual front/back texture renders confirm blue adventurer outfit, pink belt, cape, recognizable blonde hair/bow, and a curved blue crook. No additional model archive is required. The original model is low-poly, appropriate for a quick personal-use test. Exact topology/material/rig data are retained privately at `/workspace/mod-work/bopeep-stage/inspection/inspection.json` and the imported source blend there.

The source rig includes `e_cape1_m` etc and an `e_stick` prop bone; it is not the game's animation rig. A retarget/name-weight mapping to verified native Willow bones is still required. Reuse the existing source skin weights as a starting point instead of discarding them. Favor uniform overall scaling and pose alignment, retaining stylized face/limb proportions. Initial cape skinning can use appropriate existing native torso/back bones; no cloth system or new input mechanics is required for the milestone.

## Crook preserved separately

`pipeline/prepare_bopeep_prop.py` selects triangles wholly weighted to authored source `e_stick`. No triangle crosses the body/crook boundary. The working copy contains:

- BoPeep_Body:5,028vertices/6,459triangles, existing source rig/weights/UV/material.
- Crook_Preserved_NOT_EXPORTED:391vertices/590triangles, same source transform, UVs, material, source weights; hidden from initial export.
- Hidden Source_Original_UNTOUCHED collection, retaining the original combined source mesh.
- Crook_AuthoredPivot_Candidate empty at the authored source prop bone head. This is an authoring reference, not a verified native hand socket.

Saved `/workspace/mod-work/bopeep-stage/body-and-crook-v2/BoPeep-source-body-and-crook.blend`. Fresh reopening verifies exact partition of all original triangles and unchanged positions, UVs, material, weights and world transforms. Preserve the crook and future hand-attachment reference; do not implement umbrella transformation, dandelion gliding, input controls or equipment gameplay. The crook must not be merged into the playable body or impede movement/sitting/fighting.

## Willow data received and first test built

The user supplied the complete Grounded2-Willow-20261018-191911-784 extraction: 14 packages, all hashes valid, no missing dependencies. Stock Willow gameplay body/backpack each have 192 mesh-local bones and four cooked LODs. Their external skeleton/physics/animation references are preserved, rather than substituting Max's mesh-local rig.

Rigging, four-LOD writing, private materials/textures and final IoStore read-back now pass offline. The separate `zBoPeepTest_P` test awaits Windows gameplay validation. See [the current build report and instructions](bopeep-first-test.md). Do not repeat the extraction or restart Buzz.
