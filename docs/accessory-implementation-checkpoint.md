# Accessory implementation checkpoint

First-person functionality is COMPLETE by the user's report on all4skins. Working packages/head-body separation are unchanged; baseline SHA256s were rechecked. No FPtest, camera/visibility override or new skin install is requested.

User's latest crook requirements supersede earlier text: crook VISIBLE in both FP/TP, upright alongside body/screen; hide for any item in either hand. Reuse actual native spear hand positioning/attacks, ONE-handed or otherwise; TWO-HANDED requirement explicitly withdrawn. Preserve unarmed damage/stamina/reach/hit detection/timing. Do not invent a custom stance. No parasol feature yet.

## Ready Windows prerequisite

ToyStory-Accessory-Check.zip contains only the read-only ToyStoryAccessoryCheck Lua mod and instructions (3files); no cooked skins or F10override. F9once starts180second automatic0.5second sampling of exact SDK getters. UFunction parameter/return descriptor names/kinds and receiver classes are checked; enum slot numbers resolved LIVE. It follows only the previously observed CharMovementComponent/EquipmentComponent references, reads exact BoolProperty flags, and passively records stance/current attack montage when sampled. GetIsFirstPerson is read only for future FP/TP placement policy; no camera-toggle testing requested. Logs automatically to UE4SS.log.

Offline Lua5.4tests passed: automatic sampler, live enum values deliberately different from SDK, glide/hand-item/stance/montage readouts, signature rejection, property type rejection, menu/wrong receiver handling, no overlapping game-thread callbacks. Native getter safety/transitions still require Windows, since no game process is available here. Lua pcall does not contain native access violations. No new broad scans or completedV3repeat is needed. V4results were never supplied; do not invent them.

One needed test: empty both hands -> spear-only +2native attacks -> spear+shield -> shield-only -> empty -> reusable-tuft trinket glide -> landed. StartF9while standing, no airborne keypress; stopF9afterward. Return UE4SS.log and any changed action order. A very short attack may fall between samples; missing montage does not prove absence of attacks.

## Actual crook asset work completed independently

Private source /workspace/mod-work/crook-stage/grip-local-v1/BoPeep-Crook-Accessory-Source.blend independently reopened and validated. Original391vertices/590triangles, UVs and source object transform signature retained. A NEW copy uses authored e_stick grip origin, +Z shaft, uniform0.16scale (~1.648m staff). That provisional size/rotation still needs a hand/screen placement test. Source textures packed, root0rigidweights,192native reference bones retained. Originalbody/source .blend untouched.

Using proven encoder/LODwriter, created private asset /Game/_BoCrook/Art/Characters/Player_Female01/SK_Female_Teen_01.SK_Female_Teen_01:396render vertices,590triangles,4LODs,root0weights. Native skeleton bone/rest table exact. Crook namespace is isolated, no original character path override. zBoCrookAsset_P files are private staging under /workspace/mod-work/crook-stage/package-v1/mod. Retoc verify/unpack hashes passed, CUE4Parse read all4LODs, positions/indices exact, UVhalf maxerror0.0002435, normals maxerror0.003922, native UEXP legacy payload byte-exact. See crook-asset-offline-validation.json.

This is a data-only asset, NOT a spawned/attached/playable crook feature. It reuses the stable BoPeep private atlas. Original skeleton/physics/post-process references are retained by the template; an independent cosmetic component must explicitly avoid collision/physics/post-process/body animation before activation. Do not ship it as a finished weapon or equip a real spear. Next after getter evidence: validate cosmetic component creation/hand attachment and native FP/TP positioning, then equipment visibility. Attack substitution remains separate; follow actual spear montage, do not call attack RPCs.

## Wings

Six original panels remain preserved with a reversible Blender hinge prototype and exact extended geometry. Runtime wing deployment is not implemented. Once IsGliding transitions are confirmed, reuse attachment/state observer to drive simple stowed/deployed visual states without changing physics. Prototype folded containment is unverified; do not describe large hidden panels as mechanically fitted inside backpack. Do not hide native tuft until its isolated visual is identified. Future BoPeepparasol remains deferred.
