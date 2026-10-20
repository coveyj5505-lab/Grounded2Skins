# Crook carry refinement 0.2: Windows pending

The v0.1.3 direct-load/independent-component/right-hand attachment is user-confirmed visible in Windows. Preserve BoPeep-Crook-Test-v0.1.3.zip as the known working fallback. The new download contains only BoPeepCrook/Scripts/main.lua; no Paks, skins, installer, mods.txt, camera or game changes.

The accepted Bo Peep rig has sixty original wrist-dominant right-palm vertices. Their mean in r_hand_JNT local space is 3.787/.5055/-1.226 cm. Use that measured center instead of the wrist origin. A 32 cm upright origin lift moves the grip down the straight shaft, raises the hook above the hand, and lifts the bottom. Cosmetic XY scale .7 narrows the shaft; Z1.12 extends the staff. These positioning values are provisional until screenshots verify the grip.

In third person, the cosmetic inherits hand location but uses absolute rotation, updated to the actor's yaw +180, with zero world pitch/roll. The shaft stays upright through wrist rotations, with the curved hook facing forward. The lifted offset is transformed through the inverse current hand quaternion so the 32 cm lift remains upright as the arm moves. No native bone or hand pose is changed.

In first person, GetIsFirstPerson selects cosmetic-only reattachment to the existing GetFirstPersonCamera result. It uses a camera-relative forward60/right26/down40 cm origin, upright relative to the view, yaw180. Switching back restores the hand attachment and palm offset. The camera itself is never moved or changed. This addresses presentation outside the idle hand's FOV, not the solved head/body visibility split. FP placement still requires Windows screenshots; component IsVisible alone is not rendered-visibility proof.

Actual equipment slot returns still control hiding. Any item in either hand hides the crook. First/third-person switches and occupied slots are covered by Lua fixture regressions. All new native functions/signatures are validated against live metadata before calls. Six milestones and phase-specific errors remain.

Native punches, damage, stamina, timing, reach and hit detection remain unchanged. No closed-finger grip or native spear montage substitution is implemented. The upright carry orientation avoids intentionally pointing the bottom forward, but does not claim a spear attack animation. Local client only.

Test: replace main.lua with game closed. Keep existing zBoCrookAsset_P trio, Bo Peep skin and mods.txt. Load Bo Peep empty-handed, F9 once. Inspect third-person palm/hook position, first-person visibility, switch back, equip weapon/shield, then empty hands. Send UE4SS.log and screenshots. Restore main.lua from v0.1.3 to roll back.
