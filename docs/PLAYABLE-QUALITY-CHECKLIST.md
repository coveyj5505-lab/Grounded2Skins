# Playable-quality checklist

Goal: four fun, recognizable characters, then stop cosmetic development for a while. Keep working backups. Runtime assertions require Windows evidence.

## New game-build compatibility blocker

- [ ] User crash XML confirms **UE5.7.4 / Augusta-CL-3207493 / release0.6.0.3**. Prior working evidence was UE5.6 /0.316.9020.0; do not carry forward runtime or native-asset compatibility claims.
- [x] User subsequently confirms UE4SS successfully loads on the updated build. Earlier crash log stopped during StaticConstructObject scanning; do not treat that as a continuing basic-load blocker. No repeated initialization test needed. Specific accessory API access still requires live signature gates.
- [x] Initial crash requested672GiB with roughly15.8GiB physical memory available; Jessie alone reproduces a crash even without UE4SS, supporting the cooked-asset repair priority. Exact allocation origin is unsymbolized.
- [x] UE4SS/asset isolation performed: disabling loader alone did not stop crash; removing modded Paks recovered menu launch. JessieFP alone then reproduced crash and removal recovered startup.
- [ ] Audit current-build asset serialization and UE4SS support after isolation results. Preserve all released archives.
- [x] Baseline menu launch recovered after removing9 mod trios and disabling UE4SS. JessieFP alone subsequently reproduces crash; removing it restores launch. Asset compatibility cannot be assumed.
- [x] All6 original updated-build extraction archives received/verified: Max17,Willow19,Pete20,Hoops16,Shared4 packages. No collection errors.
- [x] Jessie six-mesh native rebase prepared from current5.7.4 objects. Frozen geometry/weights/UVs/FP material sections byte-exact under final native readback. Separate Jessie-UE57-Compatibility-Test.zip prepared.
- [x] User confirmed Jessie-UE57 works; Jessie release preserved unchanged. Proceed with the same current-build serialization repair for remaining packages.
- [x] Current-build private atlas material clone prepared, preserving vanilla master/subsurface imports.
- [x] Four current-build texture templates received: all8 chunks verified. Fresh private atlas/material built from5.7.4 originals,47 mip payloads independently verified. Original4096 atlas retained; test uses stock2048BC1 layout.
- [ ] Full mapped UObject runtime loading remains unverified. Native stream parsing alone is not proof of engine compatibility.

## Preserved and Windows confirmed

- [x] Buzz/Max, Bo Peep/Willow, Woody/Pete, Jessie/Hoops load and animate.
- [x] All four character first/third-person head/body visibility works. Keep this setup.
- [x] Buzz helmet fittings removed; user accepts remaining black joint areas.
- [x] Bo Peep V3 proportions acceptable for now; no further proportion pass planned.
- [x] Crook loads, attaches and is visible in both views (prior v0.2 Windows test).
- [x] Actual hand-slot contents and reusable-tuft IsGliding transitions established by earlier targeted runtime tests.
- [x] Jessie appearance and first-person behavior frozen.

## Current combined test: offline verified, Windows pending

- [x] Buzz arm source/fit comparison: remove axial/radial shape distortion; measure relaxed-pose torso clearance; preserve hands, weights, textures and 230-bone reference.
- [x] Independent native read-back of both revised Buzz meshes and unchanged other chunks.
- [x] New rigid wing assets use the Windows-loaded crook/stock accessory layout. Two visual states, independent chest attachment. Previous Commander-derived private mesh still failed to load; full cause is not established.
- [x] Both wing states independently parsed, four LODs, exact root skin, private material/texture references, fifty mips verified. Runtime load remains unverified.
- [x] Automatic accessory initialization; F6/F9 debug suspend/resume only. Menu/preview pawns wait safely.
- [x] ManualWingsExtended OR IsGliding; glide cannot be overridden by a folded preference; landing restores preference. Manual key is user-configurable and currently unassigned.
- [x] Crook actual equipment-slot hiding/restoration; unknown wrappers never guessed empty; missing IsValid method guarded.
- [x] Separate first-person source-FBX posed hand/forearm and side-of-screen upright crook; copied hand omitted during native attack or when the native hand is likely in view; optional transform failure keeps the staff-only presentation.
- [x] Cosmetic hook-first jab follows actual attack state. Native unarmed montage, damage, stamina, timing and reach remain unchanged. This is not native spear-animation substitution.
- [x] Cape upper replacement and torso-constrained upper-back cloth; lower geometry/weights/UVs preserved. Small collar/lining artifact remains visible in authoring preview; do not claim perfect neckline.
- [ ] Windows: confirm automatic startup, arm silhouette, FP grip/TP shaft contact, equipment transitions, jab, cape and wing load/deploy/retract.
- [ ] Windows: verify no duplicate first-person hand and acceptable view switching. Current runtime cosmetics are local-client only.

## Independent development while v0.3 is frozen

- [x] Separate woody-polish-next branch; released v0.3 ZIP and runtime hashes recorded and preserved.
- [x] Woody: source-weight comparison found 72 cross-leg boot-tab assignments; corrected ownership and tucked complete inner tabs toward their own cuffs.
- [x] Woody: original circular source ring restored with uniform scale; rigid spine3 weighting retained. No source geometry deleted.
- [x] Woody V2: boot/ring source and native read-back checks passed; 19 other chunks unchanged. User rejected the seated pelvis silhouette; V2 is preserved as fallback, not approved for sitting anatomy.
- [x] Buzz: first forward-flight target and disabled adapter prepared. User rejected arms near the head; that candidate is superseded, despite passing byte/atlas checks.
- [x] Buzz: independent flight-visual native read-back and private atlas preparation; 15 controller and 10 adapter Lua test groups passed. Not included in playable releases.
- [x] Bo Peep: spear-animation safety assessment updated against concrete attack/notify classes; exact recorded montage retained. Current-build montage tracks/notifies still require asset inspection. Exact-path dependency extractor prepared and locally checked; no new gameplay test requested.

## Corrected anatomy tests, Windows pending

- [x] Woody V3: source waist/hip-hinge inversion measured; raise/reweight pelvis and preserve leg length, native skeleton, V2 boots/ring, head/hands, materials and FP split.
- [x] Woody V3: actual main/backpack readback and all 50 unchanged texture mips checked; standing, running and seated front/side reviewed against rejected old seat silhouette. Synthetic FK is not game animation confirmation.
- [x] Buzz Flight V1: restore original toy arms with uniform similarity anchored to measured side-armor sockets; torso/head/wings unchanged. Cooked quarter/side views and source front view reviewed.
- [x] Buzz Flight V1: independent 192-bone root-rigid asset, four LODs, private atlas/material references verified. Optional separate automatic TP-glide adapter with restoration; concurrent wing visibility regression fixed.
- [x] Controller 17 groups and native-adapter mock 11 groups passed. Tests cover landing, FP switching, wrong pawn, signature/load failures, rollback and independent wing updates. These do not prove Windows engine calls.
- [ ] Windows: Woody standing/sitting/running and preserved first-person hands/head behavior.
- [ ] Windows: optional Buzz flight visual load, side-socket arm fit, genuine tuft glide, landing/view-switch restoration, coexistence with v0.3. Static pose, tuft visual retained, local client only.
- [x] Original v0.3 ZIP/runtime and Woody V2 ZIP remain hash-exact. No Bo Peep or Jessie changes in this correction.

## Next iterations, without delaying current test

- [ ] Buzz: convincing forward flying visual pose only while actually gliding; manually deployed standing wings must not enable it. Preserve vanilla controls/camera/physics. Current test retains the upright native glide animation.
- [ ] Bo Peep: native spear montage substitution, if it can preserve gameplay execution/notifies safely. Cosmetic jab is the simpler current alternative.
- [ ] Bo Peep: finish remaining small upper-collar artifact (additional cover-offset candidate rejected for no clear improvement) and adjust any grip offsets from actual screenshots.
- [ ] Accessories: interaction clipping and multiplayer visibility after basic states work; avoid broad probes.
- [ ] Woody: Windows confirmation of the separate boot-tab and circular-ring correction.
- [ ] Later only: tuft visual hiding, smooth wing deployment, crook/parasol glider. No need for these to perfect the current models.

## Stop point

Once major runtime features work and the user accepts the silhouettes and views, stop optional refinements. Request combined Windows checks only when a build meaningfully changes visible behavior.

## Follow-up third-party mod compatibility

- [ ] Invisible Armor: assess5.7.4 compatibility after a skin startup is restored; source/archive not supplied yet. Preserve armor gameplay; visual hiding only. User independently tested it in Paks on the updated build and it crashed.
- [ ] Teleport mod: assess separately after skin compatibility; source/archive not supplied yet. User independently tested it in Paks on the updated build and it crashed.

## UE5.7.4 remaining-package release

- [x] Woody, Bo Peep, Buzz body, crook, both wing states and corrected flight-pose mesh rebased and repacked separately. Six independent final readbacks pass geometry, skin, UV, material/export-reference and current native-tail checks.
- [x] Woody retains V3 pelvis and boot/ring fixes; Bo Peep retains cape/FP sections; Buzz retains custom 230-bone bind table and correct unique head material slot. No camera offset changes.
- [x] Private textures rebuilt using current stock templates; each private atlas set has 47 validated mips.
- [x] Isolated runtime-ue57 copies match new accessory container names and exact UTOC header/size. Released v0.3 and stable runtime preserved. Crook, wing and flight Lua regression checks pass.
- [ ] Windows: three skin trios menu, exit/relaunch and gameplay; then accessories with the updated Lua folders. Offline readback does not prove engine loading or runtime behavior.
- [ ] Windows: flight proxy load and restore on landing/view change; static corrected side-socket pose, tuft remains visible, local client only. Native spear montage substitution remains separate unfinished work.

## Latest Windows results: updated skins and accessory startup

- [x] User confirms all four current-build skins load. Woody holster clips thigh; Buzz shoulder/upper-arm placement remains poor; Bo Peep upper cape/outer weighting and inward curl remain poor; Jessie neck/head posture leans forward. Preserve current loadable packages as baseline.
- [ ] Accessory runtime blocked before Lua execution in the supplied 20:38–20:40 local-time log: UE4SS v3.0.1 Beta ca6f9b4c detects UE5.7 but cannot find StaticConstructObject, ends fatal after 2122 Lua scan attempts. No crook/wing/flight script startup markers. Prior user report of successful loader initialization does not establish this session succeeded; check whether this is the latest log before runtime or asset changes.

## Targeted loader repair candidate

- [x] User confirms failed scan log is current. Exact error traced to custom StaticConstructObject.lua override in v3.0.1 source.
- [x] Official UE5.7-capable experimental asset downloaded, CRC/AMD64/byte checked; small loader-only drag/drop candidate prepared. Old settings, mods, Paks and releases preserved.
- [x] N binding added to isolated UE57 wing config; regression uses actual config. Manual OR gliding and landing preference checks pass.
- [ ] Windows: rename failing custom override, install candidate DLLs, verify scan completes and accessory Lua starts. Then test accessory assets/states. Do not repeat gameplay while initialization is failing.

## Loader repair Windows confirmed; accessory load unresolved

- [x] Latest supplied log starts UE4SS 83330635 and all three accessory Lua mods; native reflected signature gates pass. Previous initialization failure resolved for this session.
- [ ] Crook TP asset and wing RETRACTED asset return invalid from LoadAsset_Blocking before component creation. Both disk checks found no expected UTOC in their limited standard paths; this does not establish absence from ~mods or failed engine mounting. Await exact installed folder/trio check before further loading changes. Soft-path conversion also logs an unsupported empty/subobject Utf8StrProperty; not established as the cause.
- [x] N conflicts with native hot deposit per user. Isolated config now J; manual OR gliding regression passes with actual J config. Existing released loader ZIP stays unchanged and still contains N until a new update is installed.

- [x] User confirms BOTH zBoCrookUE57_P.utoc and zBuzzWingsUE57_P.utoc are missing. Install missing accessory trios before investigating marshalling or engine asset loading. New Accessories-J ZIP includes all 9 unchanged asset files and existing 3 runtime folders, with J config.
- [ ] Windows: confirm accessory asset loading after full Paks install; automatic empty-handed crook and J/manual/glide/landing wing states.

## Accessory assets Windows confirmed, flight-controller follow-up

- [x] Latest Windows log confirms crook TP/FP assets load and component attachment/visibility succeeds. User confirms carry but FP fingers are flat/misaligned.
- [x] Both wing assets load, attach and swap correctly via J. J conflicts with game autowalk; new isolated config uses F1 (game conflict unverified).
- [x] Flight adapter remains WAIT local gameplay character in latest session. Callable reflected IsLocalController guard bug reproduced in Lua regression, corrected using Windows-working wing adapter invocation. New regression passes, remaining adapter/controller tests pass. Windows flight entry still unverified.
- [x] Glide logging now records boolean changes independently of requested visual state/manual preference. Previous log cannot rule out glide changes while manually extended. No forced gameplay glide or camera/physics changes.
- [x] FP-only crook side offset increased from43 to58 cm; TP grip/model scales unchanged; regression passed.
- [ ] FP proxy hand: repair finger curl around shaft, validate geometry before new asset release. Latest screenshot clearly shows fingers flat over staff. Not included in runtime-only update.
- [ ] Windows: F1 toggle and genuine glide/landing/FP-switch restoration with flight adapter fix; confirm side placement. Tuft visual still retained intentionally until separate visual-hiding work.

## F1 crash follow-up

- [x] User latest log ends after wing manual preference and during SetSkeletalMeshAsset on existing component. Last logged call is a lead, not a symbolized crash diagnosis. Flight adapter meanwhile polls components.
- [x] Isolated wing candidate uses fresh deferred cosmetic creation for each state instead of registered mesh reassignment; 13 mock Lua groups pass, including per-component assignment guard and stored/deployed/disposal transitions. Flight config explicitly disabled for next wing-only test. No assets, skins, loader, crook or mods.txt changed.
- [ ] Windows: standing F1 extend/retract first; then actual glide and landing only if stable. Forward flight pose intentionally disabled in this isolation package.
- [ ] Bo Peep FP hand correction clarified: upside-down orientation is main issue; flat fingers acceptable on correct side of shaft. Do not spend time curling every model's fingers.
