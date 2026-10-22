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


## Spear collection received — 2026-10-21

The targeted collector succeeded:16 packages/560053 decoded bytes, no missing requested dependencies/errors, source metadata unchanged. Every collected chunk size/SHA256 was verified locally. Current-build global script-object IDs resolve1 montage,14 animation sequences and1 skeleton. Actual AnimNotify_HitFrame exports occur in both FP/TP normal swing and charged end clips; these are verified exports, not merely names inferred from the old SDK.

The previous missing-animation-payload blocker is resolved. Next is decoding track/section/timing/notify/root-motion data and a cosmetic-only adaptation; native animation substitution is still NOT implemented. Do not request the same collection or repeat attack recording. See spear-animation-current/export-inventory.json. Released skin/hand/flight test packages remain exactly unchanged while the user tests them.

## Combined Windows feedback correction — V3

See [candidate status](feedback-v3/STATUS.md). Forward flight is now Windows-confirmed; duplicate upright body/wings and tuft remain in that test. The next candidate fixes returned-array parameter-wrapper handling using installed UE4SS83330635 source, preserving F1/manual/glide rules and the working proxy. Native spear substitution is not bundled into this defect repair.

Prepared together: Buzz elbow clearance; Bo Peep flat source hand, wrapped-grip alignment, projected right-edge placement at FOV90 and thicker staff in all3 states; lower rear cape/shoulder wrap; Woody planar/deduplicated sheriff star and38% shorter holster; higher-priority Jessie override with read-only file receipt. Four skins/all crook states pass independent native readbacks, and81 local Lua groups pass. Render review includes front/side/rear/FK pose checks and a representative16:9 FP view. Windows acceptance remains pending. Minor original vest/collar seams remain lower-priority polish.

## Buzz V3 Windows follow-up

- [x] Read new Buzz log; correlated flight teardown and restoration-pending delay with wing component replacement. See [V4 candidate status](feedback-v4/STATUS.md).
- [x] Prepare isolated incremental wing/tuft reconciliation and scoped wrist-device suppression; 44 mocked Lua groups pass. V3 unchanged.
- [x] Audit actual upper-arm weights: chest/upper-arm blending affects rigid shells. Prepare independent rigid-shell experiment preserving controlled idle placement.
- [x] Review arm experiment: rejected, raised arms still approach head despite rigid shell shape. Do not cook/ship; native pivot/armor fit remains unresolved.
- [ ] Confirm flight reliability, tuft suppression, and floating wrist-device removal in Windows after next candidate is ready. Runtime repair passes44 mocked groups; Bo Peep staff-only update passes31.
- [ ] Incorporate other three characters' incoming V3 results without restarting completed fixes.

## Woody finalized — user acceptance

- [x] User accepted the current V3 Woody skin as final. Exact trio sizes/SHA256 recorded in [accepted release](woody-final/accepted-release.json). Freeze those files; all remaining Woody cosmetic polish is removed from active work.
- [x] Bo Peep V3 body/cape accepted as good enough for now. User superseded the visible first-person hand requirement: remove added hand/forearm and use existing bare-staff view. Spear animation follows skin finalization.

## Jessie finalized — user acceptance

- [x] User accepted current V3 Jessie as final. Exact trio sizes/SHA256 recorded in [accepted release](jessie-final/accepted-release.json). No further Jessie skin or first-person changes planned.

## V4 Windows results and V5 landing repair

- [x] User accepts Bo Peep V4 presentation. Preserve current body/cape/staff-only runtime; spear animation remains next after skins. Optional FP staff shadow disable confirmed in log.
- [x] V4 Buzz still intermittent: old deployed wings AND inactive tuft components reject restoration after landing; RESTORATION_PENDING blocks subsequent glides. Exact identities/timestamps in feedback-v5/windows-v4-evidence.json.
- [x] V5 prepared: retire missing private wings on all cleanup/retry paths; live vanished tuft gets a best-effort restore, retired rejecting tuft cannot hold restoration debt. Native body/SCAB restoration remains strict.48 mocked controller/adapter groups pass.
- [ ] Windows acceptance of repeated V5 glides/landing and F1 preference restoration. Buzz-only runtime package; no skin/asset changes.
- [ ] Buzz arm pivot/armor fit remains unresolved; rejected rigid experiment must not ship.
- [ ] FreeBuild, Teleport, Invisible Armor compatibility updates remain on backlog; preserve current known-working character files while inspecting those separately.

## Current acceptance and crook animation priority

- [x] Woody V3, Jessie V3, and now Buzz V3 skin/arms accepted as FINAL. No more Buzz geometry/weight changes. Exact accepted Buzz trio recorded in buzz-final/accepted-release.json. Rejected experiments remain unshipped.
- [x] Bo Peep body/cape and V4 staff-only first-person presentation accepted. Preserve current models, crook thickness/placement, and separate persistent camera views.
- [x] Crook jab V1 prepared in isolated runtime: smooth cosmetic85-degree hook-first orientation, FP forward thrust/clearance and return, game-time pause handling,33ms polling, strict actual-slot visibility and no added FP hand.10 pure Lua motion and35 adapter/lifecycle groups pass. FP native geometry stays ahead of camera through every sampled orientation.
- [ ] Windows acceptance of crook jab V1. This animates only the independent crook; native arms still use vanilla unarmed animation. Full native spear-arm substitution remains a separate task: collected clips have gameplay hit notifies; do not play these on the gameplay animation instance without separating effects/timing. Existing clips remain collected and hash-verified; no redundant extraction.
- [ ] Buzz flight V5 still awaits Windows acceptance; no changes bundled with crook jab.
- [ ] FreeBuild, Teleport and Invisible Armor compatibility backlog remains active after character work.

## Crook jab V1 Windows feedback — reference alignment next

- [x] Current log confirms game-time reader and motion phases run; native attack windows median0.9215s. FP anchor92% resolvesright101.97cm at1440p.
- [x] Diagnose weak jab: only12cm forward stroke, held through most of native attack. Prepare isolated unpublished V2 out-and-back30cm pulse;11 curve +35 adapter groups pass.
- [ ] Use proposed real spear standing/mid-jab screenshots at same FOV to set carry/attack presentation. Do not ship another guessed FP offset. Current native arms still punch; independent staff relocation does not solve that pose mismatch.
- [ ] Full spear-arm pose adaptation remains incomplete. Keep previous collected16 packages; do not play gameplay hit notifies or change native attack mechanics.

## Crook direction update — native spear-style presentation

- [x] User supersedes upright walking-stick carry: match native spear resting angle and shaft thickness; use native spear carry/jab visual poses where practical, preserving the hook.
- [x] Review additional spear-session log: no mod RESULT ERROR; current logger does not record native spear poses. Existing16-package animation collection remains sufficient for current asset investigation; no repeated thrust test requested.
- [ ] Native spear standing/mid-thrust screenshots pending (resize to1920px wide JPEG, same FOV). Use for carry/grip/framing/diameter reference.
- [ ] Prepare visual-only native spear pose/attachment reuse with unarmed gameplay unchanged. Do not substitute a real equipped spear, run uninspected hit notifies, or represent cosmetic V2 staff-only motion as a completed spear-arm solution.
- [ ] Retain accepted skins, persistent view switching, removed FP proxy hand, and frozen releases.

## Native spear crook implementation — clarified gameplay scope

- [x] User selected native spear gameplay, then clarified damage must remain unarmed-level while reach/hit detection must act as a spear. This supersedes unarmed reach, not unarmed damage. Accepted skin work remains closed.
- [x] Prepare additive read-only SpearReferenceProbe: actual weapon attachment/mesh/bounds, camera/hand poses, montage/stance, native attack row/range and unarmed damage baseline, authority, plus current native .usmap.13 mocked groups pass; no gameplay changes.
- [ ] One new targeted reference session with this probe, then native spear presentation and scoped damage implementation. Prior thrust sessions used a logger that did not capture these fields; existing16 animation payloads need no repeat extraction.
- [ ] Confirm server/host damage behavior rather than treating a local cosmetic change as a damage override. No constant guessed damage or global weapon edits.

## Latest authoritative status — utility candidates and native damage preparation

This section supersedes older open skin-fix entries and the former unarmed-reach restriction above.

- [x] Woody V3, Jessie V3, Buzz V3 skin/arms remain final. Bo Peep accepted body/cape/staff-only appearance remains unchanged. All released character ZIPs frozen.
- [x] Received native reference capture and current .usmap. No repeat jab/animation collection needed. Native spear stance3, Spear02 visual, Spear/Spear2/Spear3 rows/range275 and unarmed Player row/range150 established.
- [x] All16 already collected animation/skeleton packages deserialize with current native mappings; montage sections/blends recorded in [native evidence](native-spear-next/evidence.json). No unsafe gameplay montage substitution shipped.
- [x] Supplied FreeBuild, Invisible Armor and Teleport archives unpacked and original hashes recorded. [Utility test instructions](utility-updates/README.md).
- [x] FreeBuild isolated host/game-thread/schema-checked autocomplete replacement, preserving supplied behavior and crafting settings.
- [x] Invisible Armor isolated render-only Lua replacement; four native armor fields confirmed by supplied mappings. No146-mesh old Pak override required. Accepted body/SCAB visibility unchanged by design.
- [x] Teleport confirmed TOC/header identity mismatch repaired; both original Blueprint chunks preserved exactly, retoc/re-extraction checks pass, both packages including script bytecode deserialize using current mappings. Windows behavior remains unconfirmed.
- [x] Seven actual-Lua utility fixture groups pass. Separate utility ZIP prepared; no changes to character release files.
- [x] Native damage parser rejects unknown/zero baselines, malformed values, mismatched row counts and nonuniform charged/combo ratios. One-shot read-only native damage probe prepared; five Lua fixture groups pass. No combat writes shipped.
- [ ] Crook native spear gameplay implementation is **not complete**. Damage helper's0 does not establish fist damage, whether or not a target was hit. Attack table damage values remain absent from received outputs; targeted automatic row read is required before promising correct unarmed-level damage.
- [ ] Bind thicker hooked crook to actual native weapon visual frame and preserve native spear collision/range/animations, after choosing a correct authoritative damage route. See [implementation preparation](../runtime-native-spear-next/README.md).
- [ ] Windows validation of utilities, including Teleport controller/map/exit, still required. Parsing does not prove Blueprint compatibility or multiplayer behavior.
- [ ] Buzz flight V5 acceptance remains pending independently; no new flight or skin changes in utility package.
