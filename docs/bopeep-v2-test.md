BO PEEP V2 -> WILLOW: HANDS AND CAPE TEST

Offline validated; this new build has NOT yet been tested in Grounded 2.
PC Game Pass / WinGDK build 0.316.9020.0. No UE4SS required.

INSTALL
1. Close Grounded 2.
2. Move all THREE old zBoPeepTest_P files OUTSIDE Augusta/Content/Paks. Keep them as your fallback. Also remove any other Willow replacement from Paks. Do not install Bo Peep V1 and V2 together.
3. Copy the three zBoPeepV2_P files from mod directly into Augusta/Content/Paks.
4. Select Willow. Test idle hands, walking/running, crouching/jumping, sitting, punching and holding weapons/shields. Compare fingers and upper cape with the old build.
5. Keep Buzz, Jessie and Woody installed. Their files are unchanged.

REMOVE / REVERT
Close the game and remove only the zBoPeepV2_P trio. Restore the saved V1 trio if desired. No original game files are overwritten.

WHAT CHANGED
Hands retain the supplied model's recognizable finger shapes using coherent, mostly rigid hand weighting. The game's individual finger curls no longer stretch these fingers. Fine finger articulation is simplified; precise closed fists and weapon grips are not promised. This prioritizes stable-looking hands.
The cape now has a single consistent torso fit and weight assignment, removing its mixed arm influence. It is intentionally stiff, without new cloth simulation or collision. Some chair/body clipping can remain.
Face, hair, outfit, legs, UVs, textures, materials and native skeleton are preserved outside the hand/cape correction masks. No crook, spear animation, equipment logic, inputs, gliding or gameplay change is included.

VALIDATION
Fresh Blender reopen, normalized skinning, six independent FK pose/read-back comparisons, +/-75-degree finger stress tests and exaggerated arm/cape isolation tests passed. Source crook geometry, UVs, materials, weights and transform remain exactly preserved and excluded from gameplay. All 28 cooked LODs across seven meshes read independently; geometry/weights/UVs/section checks and 50 texture mip/dependency checks passed. Previews are authoring or actual cooked readbacks, not in-game screenshots. Only your Windows test can confirm the new appearance in actual animations.

REPRODUCTION
Preserved V1 scene: /workspace/mod-work/bopeep-stage/rig-v2/BoPeep-Willow-skinned.blend. New stage: /workspace/mod-work/bopeep-v2-stage.
1. correct_bopeep_v2.py NEW_FIT on the preserved scene produces fit-v1/BoPeep-Willow-V2.blend and expected masks/arrays.
2. review_bopeep_v2_poses.py NEW_POSES and render_bopeep_v2_details.py STAGE create controlled pose and hand/cape previews. validate_bopeep_v2.py STAGE independently reopens and compares the saved mesh, source prop partition and NumPy LBS; checks +/-75-degree finger stress and cape isolation.
3. Reuse export_bopeep_geometry.py, native_buffers.py, write_willow_lods.py, assemble_bopeep_zen.py and original private-templates-v1. Preserve the existing stock Willow skeleton/physics references. Repackage with repackage_iostore.py --mod-name zBoPeepV2_P.
4. readback_bopeep_package.py and validate_bopeep_final.py check the final container; native-buffer-probe reads tangent frames and render_cooked_bopeep_preview.py renders the independently decoded mesh/atlas. validate_bopeep_v2_package.py STAGE proves only two body chunks change while fourteen private texture/material/bulk and hair chunks remain exact V1. All four other baseline ZIP hashes remain unchanged.
Final output stages: fit-v1, poses-v1, geometry-v3, buffers-v1, cooked-v1, raw-v1, package-v1, final-check-v1, frames-v1. Texture/atlas/stock links are read-only references to V1; original reference files, source rig, source crook and original materials remain unchanged. All outputs require new directories.

OBSERVED SCOPE
723 hand-region vertices and936 cape vertices are corrected;3369 other vertices retain exact V1 positions/weights. UVs/materials/topology are exact. Finger stress displaces hand surfaces0m; cape arm stress displaces cape0m. Six independent saved-pose LBS comparisons agree within3.46e-7m. Native bones/rest tables remain exact in cooked files. Neutral BC5 normal mips independently decode to RG128, and tangent/normal components read back within0.003922 with exact signs. These checks do not prove game collision-free cape behavior or perfect weapon grips.

NEXT PRIORITY
User explicitly requested a completed, good-looking Bo Peep with good fingers before crook work. Deliver this separate test first and use Windows feedback to assess hands/cape before starting runtime accessory changes. No crook/UE4SS implementation has been added.
