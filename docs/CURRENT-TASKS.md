# Current Toy Story tasks

## Confirmed baseline to preserve

- All four UE5.7.4 skins load; solved first/third-person head/body visibility stays intact.
- Updated UE4SS starts.
- Buzz: F1 manual wings, automatic glide deployment, landing restores manual preference. Buzz-Wings-F1-Recreate-Test.zip is confirmed.
- Bo Peep: crook loads, empty-hand carry/equipment hiding implemented, repeated FP/TP transitions now user-confirmed. BoPeep-Crook-Persistent-Views-Test.zip is confirmed for view switching. Extended attack/equipment/interaction and multiplayer checks remain separate.

## Skin/geometry fixes

1. Buzz: shoulders/upper arms attach at wrong armor locations. Compare source, fitting/rest pose, weights and cooked mesh; preserve recognizable suit proportions.
2. Bo Peep: repair torn/disconnected neckline/shoulders, inside curling and stiff outer cape apparently following hands. Preserve acceptable body proportions and lower cape where possible.
3. Jessie: correct forward-strained neck/head posture without damaging working doll proportions, chaps, face/hat/hair and first-person behavior.
4. Woody: move/reweight holster to avoid thigh clipping. Keep existing boot/ring corrections; no additional defect in those confirmed in latest screenshots.
5. Bo Peep accessory hand: turn upside-down FP proxy hand correctly beside shaft. Flat grip accepted; no all-character finger-curl project. Keep one connected hand/forearm, prevent duplicate native limbs.

## Runtime/accessory work

1. Bo Peep FP presentation: confirm/finalize farther-side and taller appearance using separate FP placement; no global TP scale or camera changes. Current closer-perspective adjustment awaits acceptance.
2. Buzz flight visual: stable forward pose only during actual glide, arms away from overhead tuft grip, restore on landing/first-person. Disabled currently; a source candidate exists but has not passed Windows flight validation. Preserve confirmed wing behavior and physics/controls/camera.
3. Buzz tuft visual: hide only relevant Buzz glide tuft, restore appropriately; preserve trinket and physics. Not implemented.
4. Bo Peep attacks: native spear animation substitution if safe; current cosmetic jab retains vanilla unarmed execution. Recorded montage AM_Player_Character_Attack_Spear_01_Augusta; no real spear or artificial attack RPC. Native timing, reach, collision, stamina, damage unchanged.
5. Bo Peep carry: verify third-person palm contact, return-to-upright after attacks, equipment/shield/handheld hiding and interaction clipping with persistent view components. Fix remaining visible issues without undoing lifetime fix.
6. Accessories multiplayer: local-client visuals currently; establish what each player sees, then address replication/presentation only if necessary for shared play.
7. Packaging: consolidated tested skin+accessory release after visual fixes; drag/drop only, preserve versioned rollback packages.

## Other mods

- Invisible Armor: update for UE5.7.4; old Pak independently crashed. Need original archive/source. Visual hiding only, keep armor gameplay.
- Teleport: update for UE5.7.4; old Pak independently crashed. Need original archive/source.
- FreeBuild: old version removed; optional later compatibility validation/update if requested. It did not explain the earlier loader scan failure.

## Deferred extras

- Smooth/telescoping wing transition beyond reliable two-state visuals.
- Bo Peep crook-to-parasol glider.
- Cosmetic polish beyond obvious defects.

Suggested order: FP hand orientation + major body/cape fixes; Buzz flight pose; tuft hiding and safe spear animation; combined validation and final release. Work that does not depend on a test can proceed independently.

## Latest user priority

One short optional enable-only flight-visual test first because the candidate already exists. Then prioritize all four skins' obvious defects, including Bo Peep FP hand orientation, followed by Buzz flight refinements. Do not let an unsuccessful flight test delay skin corrections. Preserve working wing and crook baselines.

## Current prepared iteration — 2026-10-21

Authoritative evidence: [visual review](skin-fixes-next/visual-review.json), [downloads and hashes](skin-fixes-next/downloads.json).

- [x] Buzz shoulder attachment candidate: original source/component correspondence and rest matrices audited; proximal cap repositioned toward side armor, blend limited to avoid compression; final native front/side/raised-arm previews personally reviewed. Await Windows animation acceptance.
- [x] Woody holster candidate: source holster groups isolated, spine1 attachment changed to Hips, moved outward1.5–3cm; actual cooked quarter/seated renders reviewed. Boots/ring unchanged. Await Windows.
- [x] Jessie neck candidate: head/hat/hair moved back6cm with blended neck; no weight/reference/face redesign; actual cooked side/front reviewed. Await Windows.
- [x] Bo Peep cape candidate: continuous source topology restored, inner/outer layers separated, torso/pelvis cloth weights avoid hand attachment; first cooked review still showed collar gaps, second revision added small rear collar underlay and reviewed closed gaps. Lower cape retained. Await Windows.
- [x] Crook FP hand candidate: upright original hand, rebuilt connected short forearm, corrected palm-matched skin texel; close and representative FP perspective reviewed. FP65/right50/down32, TP unchanged. Native readback passes; persistent camera-switch lifecycle unchanged. Await Windows.
- [x] All four skin candidates and accessory: every inline LOD, native reference/material records, geometry/UV/weights/colors and unrelated chunk preservation checked after repacking. No claim that offline checks establish Windows behavior.
- [x] Flight source-access candidate: added validated Character.Mesh path in addition to owned components, deduplication and exact source-asset logging. Existing corrected horizontal flight asset preserved. Optional tuft route reads InventoryComponent.UsingGliderItem (Glider-slot fallback) -> Item.GetItemVisuals -> primitive render components; live metadata gates and independent failure handling. Exact visibility restoration included. Await actual Windows execution; tuft path is an SDK lead until verified.
- [x] Regression run:27 crook lifecycle/access groups,13 wing groups,17 flight-adapter groups and19 flight-controller groups pass locally. Mocked Lua does not prove native function calls.
- [ ] Native spear animation: existing montage path confirmed; required current-build animation payloads absent from previous character extracts. Do not touch native attack execution or play uninspected gameplay montage. Current hook-first cosmetic jab remains the practical fallback. Targeted read-only dependency collector prepared; no repeated attack recording needed.
- [ ] Windows acceptance of skin deformation, hand presentation, flight creation/landing/FP rollback and optional tuft visibility.
- [ ] Multiplayer appearance of local cosmetic components remains unverified.

The original v0.3, confirmed F1 wing release and confirmed persistent-view crook release remain frozen. Stable flight config remains disabled; only the isolated flight test ZIP enables the candidate. No BuzzWings runtime changes in this iteration. No new claim that remaining work is final/game-proven.
