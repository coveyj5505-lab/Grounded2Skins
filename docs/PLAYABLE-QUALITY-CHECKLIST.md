# Playable-quality checklist

Goal: four fun, recognizable characters, then stop cosmetic development for a while. Keep working backups. Runtime assertions require Windows evidence.

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
- [x] Woody: standing/running/sitting FK checks and independent main/backpack cooked read-back passed; 19 other chunks unchanged. Separate Woody-Boots-Ring-V2-Test.zip prepared; Windows confirmation pending.
- [x] Buzz: offline forward-flight target prepared with extended wings; source geometry/rest/weights unchanged, reset checked. Runtime adapter still pending.
- [x] Bo Peep: spear-animation safety assessment updated against concrete attack/notify classes; exact recorded montage retained. Current-build montage tracks/notifies still require asset inspection. No new gameplay test requested.

## Next iterations, without delaying current test

- [ ] Buzz: convincing forward flying visual pose only while actually gliding; manually deployed standing wings must not enable it. Preserve vanilla controls/camera/physics. Current test retains the upright native glide animation.
- [ ] Bo Peep: native spear montage substitution, if it can preserve gameplay execution/notifies safely. Cosmetic jab is the simpler current alternative.
- [ ] Bo Peep: finish remaining small upper-collar artifact and adjust any grip offsets from actual screenshots.
- [ ] Accessories: interaction clipping and multiplayer visibility after basic states work; avoid broad probes.
- [ ] Woody: Windows confirmation of the separate boot-tab and circular-ring correction.
- [ ] Later only: tuft visual hiding, smooth wing deployment, crook/parasol glider. No need for these to perfect the current models.

## Stop point

Once major runtime features work and the user accepts the silhouettes and views, stop optional refinements. Request combined Windows checks only when a build meaningfully changes visible behavior.
