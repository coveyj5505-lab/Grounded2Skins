# Buzz / Bo Peep combined playtest v0.3

Current Windows test pending. This build keeps Jessie/Woody and the solved character first-person visibility unchanged. It contains files only, with four separately removable Pak trios and two independent Lua mods.

## Windows evidence and current choices

The supplied log reached native wing soft loading but returned an invalid retracted mesh. No wing component, attachment, visibility or deployed-state operation ran. The prior exact-name dependency fix was insufficient; the full load failure cause is not established. The new isolated wing packages reuse the actual stock-derived native layout already loaded successfully by Bo Peep's crook. Buzz's body still retains its original 230-bone animation skeleton; root-rigid accessory meshes carry the proven 192-bone template without animation or leader-pose binding. New namespace/container names separate this attempt from old files, and a read-only TOC header/size check reports the installed revision before native loading.

Buzz's six arm components are compared against the untouched source before editing. The old upper-arm fit scaled length around0.80 and radius1.02, with70mm shoulder/20mm elbow offsets. New similarity fits preserve source armor shapes; a controlled relaxed-pose torso measurement then places their centers at the torso edge, fading correction toward unchanged wrists/hands. This is a visual fit to the original bones, not a new skeleton or a guarantee for every animation. Both cooked variants independently match intended geometry/weights/UVs/frames. A fresh Blender reopen compares59,364 cooked/source triangle corners (max error1.34e-7m) and restores actual cooked normals for the previews.

Bo Peep's original source/V3 body vertices remain preserved. Only147 broken upper-cape triangles are replaced, adding a thin closed blue shoulder/back sheet. Upper-back cloth is constrained to spine3; light upper lining/edge UVs are simplified to existing blue texture pixels. Lower-cape positions, weights and UVs remain unchanged. A small collar artifact/overlap remains in the preview; this is an incremental test, not a perfected cape. Her accepted proportions are not refitted. Native head-section membership remains2650 triangles. All14 non-mesh chunks remain byte-identical.

The first-person crook has a baked copy of her actual source FBX hand/forearm. The accepted playable hand was intentionally made rigid in V2, so posing its native finger bones could not close it; the new independent viewmodel instead uses the preserved FBX semantic finger weights and FK. This leaves the character's existing hand and animations untouched. The viewmodel is camera-relative75cm forward/43cm right/32cm down, with independently sized crook geometry; third-person staff size remains the previous baked0.7XY/1.12Z proportions. Its origin is moved to the actual shaft-contact point, and the hand attachment point moves2.63cm toward the native middle-finger root. Source hand/forearm viewmodel placement still needs Windows validation, including armor and view transitions.

During native bIsAttacking, the cosmetic crook pitches forward hook-first; FP swaps to the identical staff-only mesh so the copied hand does not duplicate the native punching limb. Afterward it returns upright with its copied grip. A conservative camera-space check also omits the copied hand when the native hand is likely already visible; optional transform-check failure falls back to the staff-only presentation. These presentation checks still need Windows validation. This is a cosmetic jab, not substitution of AM_Player_Character_Attack_Spear_01_Augusta. Native unarmed montage, damage, reach, hit detection, stamina and timing are untouched. Optional attack getter failure leaves carry/equipment recording active. Unknown equipment wrappers are rejected rather than interpreted as empty.

Both Lua mods start automatically and wait for gameplay actors. F6/F9 are debug suspend/resume only. Wings select deployed = ManualWingsExtended OR IsGliding. The selected preference survives landing; toggling a preference cannot fold wings during an active glide. Scripts/wing_config.lua exposes the initial preference and an optional key name; the key is currently unassigned pending the user's choice. The tuple logic and startup/menu transitions pass real Lua5.4 mocked-object tests, which do not replace Windows testing. No forward flying pose, native spear montage substitution, tuft visual hiding or multiplayer accessory replication is included. These remain on PLAYABLE-QUALITY-CHECKLIST.md.

## Drag and drop

Close the game. Back up/move the previous Buzz BODY trio (currently zBuzzClean_P, or an older zBuzzFP_P variant), previous Bo Peep BODY trio (currently zBoPeepV3_P), and old zBuzzWings_P trio outside Paks. Do not leave two versions of either body skin installed.

Copy all twelve files in Paks to Augusta/Content/Paks. Copy the two mod folders to Augusta/Binaries/WinGDK/ue4ss/Mods, replacing the existing main.lua files and adding wing_config.lua. Keep both existing mods.txt entries enabled. Keep zBoCrookAsset_P and all Jessie/Woody files; no installer or mods.txt is supplied.

The new trios are zBuzzArmsV3_P, zBuzzWingV2_P, zBoPeepV4_P and zBoCrookV3_P. Do not press F6/F9 for normal operation. Check Buzz standing/arms, open the reusable tuft using Shift from sufficient height, land; check Bo Peep empty hands, either equipped slot, empty again, both views and a few attacks. Send UE4SS.log and screenshots. One session may test both characters; the modules log independently.

Rollback: close game, remove the four new trios, restore the backed-up body files and previous Lua scripts. Stable ZIPs and originals remain unchanged, as recorded in playtest-v03-preservation.json.

## Reproduce from retained stages

Toolchain: Blender4.3.2 CPU, retoc0.1.5, existing CUE4Parse Grounded2 native probes on .NET10; Lua5.4 fixture runner. No new Unreal project or SDK offsets.

Buzz: refine_buzz_arm_similarity.py -> preview_buzz_arm_refinement.py -> clear_buzz_arms_in_relaxed_pose.py -> native_buffers.py -> rewrite_measured_native_lods.py -> repackage_iostore.py -> readback_buzz_package.py -> validate_measured_mesh_rewrite.py -> verify_buzz_arm_cooked_blender.py / cooked preview.

Cape: replace_bopeep_broken_upper_cape.py on the preserved V3 scene -> export_bopeep_geometry.py -> existing head-material threshold split -> native_buffers.py / measured writer / proven packaging/read-back -> measured validator. The two source profiles are from V3; material imports and every original reference-bone byte remain intact per mesh variant.

Crook: author_crook_grip_viewmodels.py -> exporter for TP/FP -> build_crook_grip_packages.py (staff-only attack view derived by retained source-vertex IDs) -> proven packing/read-back -> validate_rigid_accessory_set.py.

Wings: build_wings_from_proven_accessory.py consumes existing validated chest-local wing atlas geometry, retains all material/texture bytes, and packages using the working stock accessory layout. Read-back validates both four-LOD meshes, exact package/export paths, private MI/public hashes and50 texture mips. The original six panels and states remain preserved in the existing wing authoring scene.

Current private stages: /workspace/mod-work/refinement-next/buzz-arms-v1; bopeep-cape-v4h; crook-grip-v3d; crook-package-v3; /workspace/mod-work/wings-stage/proven-layout-v3 and proven-package-v2. Source .blend files and packed images remain there. Rejected cape/arm candidates are private history and are not installed by this ZIP.
