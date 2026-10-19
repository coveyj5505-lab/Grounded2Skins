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

## Native Willow data required

Current workspace has stock Max and custom Hoops/Max references, not original Willow skeletal packages. Max's actual stock imports include `/Game/_Augusta/Art/Characters/Player_Female01/Materials/MI_Eye_Occlusion_Mike_fem01_Willow`, corroborating the character directory but not verifying its mesh/skeleton filenames. Do not assume Willow's bone count, bind transforms, physics or native LOD layout match Max or Hoops.

`Willow-Compatibility-Extractor.zip` discovers actual indexed SK mesh paths under Player_Female01 (including hair), then reads their actual Zen imported-package names and follows skeleton/physics dependencies, including paths outside the character directory. It uses exact original Augusta-WinGDK.utoc/adjacentUCAS, not installed mod override context. No guessed SK_Female_Teen filename or assumed physics name. No full archive copy, texture dump, game modification or injection. Max material/texture templates are already available for private Bo Peep clones, so original Willow textures are not requested initially.

Use the same working Windows retoc0.1.5/Python3.11+ tools: extract helper, run Start-Extraction.cmd, select retoc.exe and original game UTOC, upload Desktop Grounded2-Willow-[timestamp].zip. The wrapper now creates a ZIP for explicit partial reports as well as complete results; use the available chunks rather than demanding a repeat/full extraction. It caps selected decoded data at48packages/128MiB and records hashes and unchanged source size/mtime.

The discovery/extraction driver was actually run on the known Commander reference:5SkeletalMesh packages plus1PhysicsAsset were extracted (31,542,177decodedbytes), headers parsed with no warnings/errors and the two unavailable original skeleton imports correctly recorded. A default Female01 scan against the same reference yields zero packages/partial status, so Max assets are not falsely identified as Willow. These are tool controls, **not actual Willow evidence**. The Windows GUI is derived from the user's working Max launcher and cannot be run in this Linux environment.

After the user supplies Willow chunks: verify hashes/classes/native skeleton and LOD layout; adapt only template-specific serialization offsets/hash guards as needed; map source skin groups to native bones; preserve proportions and hide the original Willow hair appropriately; use a separate Bo-Peep private material/texture namespace and mod basename so Buzz remains simultaneously usable. Package and independently read back before a Windows test. No installable Bo Peep mod exists yet; the concrete blocker is the missing original Willow dataset.
