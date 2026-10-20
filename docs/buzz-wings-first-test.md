# Buzz wing visual states: first Windows test

Windows pending. Working Buzz body/head sections, textures, proportions and native skeleton remain unchanged. The Bo Peep crook v0.1.3 ZIP remains untouched and is now user-confirmed visible in third person.

The separate wing accessory uses all six preserved extended panel objects. New stored copies compress/nest inside the backpack instead of using the earlier protruding hinge prototype. Original meshes/UVs/transforms and the accepted body are exact in the new Blender file. Rear/side/quarter previews are genuine CPU Blender renders, not game screenshots. Stored surfaces were sampled from eight horizontal viewpoints; all sampled rays were occluded by the original body/backpack. This is not collision or all-pose clearance certification.

Separate chest-local deployed/stored cooked meshes attach to chest_JNT as a collisionless, animation-disabled local cosmetic. IsGliding() true selects deployed; false selects stored. No inventory, combat, physics, camera or existing skin writes. State polling is 200 ms. F6 toggles the test component. Crook F9 remains independent. Other multiplayer clients do not automatically receive this local component. The tuft visual remains unchanged. Transition is an immediate state swap, not a hinge animation.

## Drag and drop

Game closed: copy the three files inside Paks into Augusta/Content/Paks. Copy BuzzWings into ue4ss/Mods and add `BuzzWings : 1` to mods.txt. Keep all four working skins and crook files installed.

Load as Buzz/Max. F6 once. Inspect retracted backpack, glide using the reusable tuft, then land. No airborne key presses. F6 again removes the accessory. Send UE4SS.log and rear screenshots. Six native lifecycle milestones are logged; errors include phase and last native function. Windows load/attachment/alignment remain unverified until this test.

Remove only BuzzWings : 1/the BuzzWings folder and zBuzzWings_P.{pak,utoc,ucas} to roll back. Do not remove the Buzz body skin.

## Verified offline

- Fresh Blender reopen: body and all twelve preserved source/fitted wing objects exact; 230 rest bones unchanged; packed source textures retained.
- Synthetic chest rotations -25/0/25/45 degrees: rigid state deformation error below 1.4e-7 m.
- Deployed 826 render vertices / 328 triangles; stored 818 / 328; seam splitting accounts for vertex difference.
- Retoc verified and re-extracted all 12 chunks / seven private packages. No original body, crook or shared game asset overrides.
- Fresh CUE4Parse native mesh reads: positions, indices, weights and UV quantization exact; reference bones/rest exact; normals within quantization tolerance.
- Native material slot0 resolves to the new private MI and four private textures, validated via actual imports/public export hashes and serialized texture parameters.
- Fifty texture mips independently read/hash checked. BC3 RGBA mean absolute error 1.175/255. Flat BC5 RG128 across every mip, avoiding the old stripe issue.
- All seven packages converted to legacy with zero failures. Both actual self-package/export object paths agree with runtime requests.
- Eight Lua controller regressions pass: stored/deployed/stored transitions, no redundant swaps, activation while gliding, missing assets, invalid glide state, wrong pawn, signature failures and cleanup.

Source project: /workspace/mod-work/wings-stage/states-v2/Buzz-Wing-States.blend. Reports and reproducible scripts are tracked; private input assets remain under mod-work.

## Reproduction

Author: prepare_buzz_wing_states.py; fresh reopen/export: validate_export_buzz_wings.py; source-texture previews: render_buzz_wing_states.py. build_buzz_atlas.py now accepts --max-repeat 16 for the high-repeat original wing UVs (default 4 remains unchanged). native_buffers.py and write_buzz_atlas_textures.py are reused. isolate_buzz_material_zen.py accepts private namespace/tag options with unchanged defaults. build_buzz_wing_zen.py creates the isolated seven-package store. repackage_iostore.py and readback_buzz_package.py perform the proven packaging/readback workflow; the latter accepts --texture-prefix T_Wng. validate_buzz_wing_package.py verifies native reads, material dependencies and pixels. Runtime checks: python pipeline/test_buzz_wings_runtime.py.
