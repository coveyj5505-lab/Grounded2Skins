# Playable-quality checklist

Goal: four fun, recognizable characters, then stop cosmetic development for a while. Keep working backups. Runtime assertions require Windows evidence.

## New game-build compatibility blocker

- [ ] User crash XML confirms **UE5.7.4 / Augusta-CL-3207493 / release0.6.0.3**. Prior working evidence was UE5.6 /0.316.9020.0; do not carry forward runtime or native-asset compatibility claims.
- [ ] UE4SS v3.0.1 Beta fails StaticConstructObject scanning before accessory Lua startup. Crash requests672GiB with roughly15.8GiB physical memory available; exact cause not established.
- [ ] Isolate UE4SS from cooked assets by temporarily renaming only the game-local WinGDK/dwmapi.dll loader; retain Paks for that one menu-only test. Local loader path is confirmed by crash module list.
- [ ] Audit current-build asset serialization and UE4SS support after isolation results. Preserve all released archives.
- [x] Baseline menu launch recovered after removing9 mod trios and disabling UE4SS. JessieFP alone subsequently reproduces crash; removing it restores launch. Asset compatibility cannot be assumed.
- [x] One-run read-only four-character extractor prepared and locally tested;6 output ZIPs, no server entry or UE4SS required. Current5.7.4 raw asset collection pending.

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
