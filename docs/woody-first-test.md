CURRENT WINDOWS STATUS: user confirms Woody skin works in third person; head obstructs first person. Preserve this original ZIP as the tested baseline. See first-person-section-repair.md for a separate candidate update. The original release instructions below retain their pre-test wording as history.

WOODY -> PETE: FIRST WINDOWS TEST

Offline validated; NOT yet tested in Grounded 2. Target: PC Game Pass / WinGDK 0.316.9020.0.

INSTALL
1. Close Grounded 2.
2. Move any other Pete replacement files OUTSIDE Augusta/Content/Paks. Keep Buzz, Bo Peep and Jessie installed.
3. Copy the three zWoodyTest_P files from mod into Augusta/Content/Paks.
4. Select Pete. Test walking, running, sitting, crouching, jumping, punching, weapons/shields, backpack toggles and character selection.
5. To remove, close the game and remove only the zWoodyTest_P trio. No original game files are overwritten.

LIMITS
Simplified opaque matte material, flat normal map, no cloth physics or new face animation. Original voices/portrait remain. Doll hands are predominantly rigid for stability; exact equipment grip is untested. Scarf/holster and shoulder regions may clip in untested poses. Four full-detail LODs favor a first test over optimization. Original Pete hair/glasses are hidden; special left/right ArmPeeper meshes are hidden too, so those particular peeking views may lack hands. First-person and special-state appearance need your test. Crook, wings and gameplay logic are not involved.

All original source meshes, rig, shape keys and twelve maps are preserved privately. Private Woody materials/textures are isolated from the other characters. The supplied brown eye artwork is remapped into a simple eye composite. Previews are synthetic authoring poses plus actual cooked asset readbacks, not in-game screenshots.

ACTUAL VALIDATION
17 packages /22 chunks; all independently unpacked bytes match staged hashes. CUE4Parse reads 48 LODs across twelve native meshes. All original mesh-local bone tables/rest transforms are byte-exact stock. Main and backpack bind 188 bones; character selection has the same used-name prefix with 187 bones (only unused FPSpine_Pelvis absent). Hair/glasses and the two ArmPeeper meshes are invisible stubs; each keeps its own original skeleton. Intended positions, indices, skin weights, UVs, colors, sections and all repeated LODs match independent native readback. Private MI resolves the four private texture dependencies and original material parent; all 50 mip records/hashes check. Decoded BC3 atlas mean absolute RGB error is 1.385; every neutral normal mip decodes to RG128 without stripes. Tangent/normal component error is under 0.0041 with exact handedness. Final source scene fresh-reopened and all six FK poses independently agree with NumPy LBS below 0.00000034m. Actual cooked decoded front/side previews inspected. These are offline checks, not a Windows runtime claim.

REPRODUCTION
Private /workspace/mod-work/woody-stage retains source and all diagnostics. Accepted pipeline: rig-v4 -> gameplay-v1 (original-art atlas-v1) -> geometry-v1 -> buffers-v1 -> cooked-v1 -> templates-v1/raw-v1 -> package-v1 -> final-check-v1. Use rig_woody_blender.py, create_woody_atlas.py, prepare_woody_gameplay.py, export_woody_geometry.py, native_buffers.py, write_pete_lods.py, clone_woody_material_templates.py, assemble_woody_zen.py, repackage_iostore.py --mod-name zWoodyTest_P, readback_woody_package.py and validate_woody_final.py. review_woody_poses.py and validate_woody_rig.py check saved source fits. All writers require new output directories. Preserve stock native bone bytes and original shader payloads; do not arbitrary-cook a new UE project. Source shape keys are retained on originals and removed only from playable copies to prevent Basis data overriding fit.

NEXT AUTHORIZED PHASE
Bo Peep hands/cape correction, then actual UE4SS compatibility/object-inspection Windows probe and crook carry/spear/equipment state investigation. New request retained in bopeep-next-phase-user-requirements.md. Wings and parasol remain future work; do not implement gliding yet. User has UE4SS downloaded, but exact version/loading evidence are still needed.
