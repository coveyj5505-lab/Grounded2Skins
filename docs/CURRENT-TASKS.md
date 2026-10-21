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
