# Native spear crook preparation — not an installable gameplay mod yet

User-approved direction: actual native spear grip/carry/jab and spear reach/hit detection, with unarmed-level damage. Native spear gameplay supersedes the former unarmed range requirement. Accepted skins and existing releases remain untouched.

The `damage_rows.lua` module reads/normalizes native exported damage data and rejects an unknown/zero unarmed baseline, missing/misaligned table data, and a single multiplier that would give different damage on different combo or charged profiles. It performs no native writes and is not a completed crook implementation.

Received capture confirms the real Spear02 static-mesh visual, native spear animation stance3, native spear attack rows Spear/Spear2/Spear3 and275 range, versus unarmed Player row and150 range. Native helper returned0 without measuring hit damage. No target collision was captured, but target hits were not needed for the intended baseline data collection.

Outstanding:

1. Read native DamageData/ChargedDamageData/PerfectChargedDamageData values. The narrowly scoped SpearDamageProbe does this automatically after world load; no additional attack recording or mappings dump is needed.
2. Choose a correct authority-side damage implementation from actual profiles. A generic multiplier must not be claimed correct if combo/charged profiles differ. Native ResolveAttack/ResolveAttackForHitResult are research leads, not proven hooks; direct C++ execution can bypass reflected hooks.
3. Bind the crook proxy to the real native weapon component, using the native arm animations and existing item attack execution. Keep original weapon collision/hit traces, hide only its render, and preserve independent stable view components/accepted skins. Correct the earlier GetLocalBounds signature (`min`/`max`, not `Min`/`Max`) before using native bounds as fit data; reject unavailable bounds instead of guessing them.
4. Fit shaft diameter/length and hook orientation against the native weapon. The collected native weapon-to-hand relationship varies across FP poses, so a constant camera offset or fake arm is unsuitable.
5. Validate normal/charged damage, host/client authority, FP/TP transitions, equipment changes and rollback in Windows. Do not label the old independent timed staff rotation a native spear solution.

## Current result and scope — 2026-10-22

The latest Windows probe completed: Player/Player2 normal8; Spear/Spear2/Spear3 normal20. User clarified the crook has **normal jabs only, no charge attack**. Charged attack damage is therefore outside the supported behavior. Use normal-only multiplier0.4, after disabling charging specifically for the crook. Do not impose a per-attack charged-damage implementation as a blocker or add charging. The pure normal-only resolver and fixtures reflect this decision; it is not yet a native state implementation.

The damage-value blocker above is resolved. Current cooked attack-table and Spear02 mesh baselines are still needed to prepare correct native weapon fitting and charge settings. The new native-baseline collector collects those together with current controller/map/teleporter packages for Teleport repair. It does not collect the existing animation payloads or .usmap again.

## Native asset preparation received and validated

All eight requested native baselines are now available; do not request them again. The current attack table has been cloned into private `/Game/Blueprints/Attacks/BoPkAttacks`. Its three spear combo rows read back with Damage8, Range275, ChargeTime0 and charged/perfect Damage0. All425 rows and unrelated fields are otherwise unchanged. This is a private-table route, so an additional0.4 multiplier must NOT be applied on top of it. Ordinary native ItemAttacks/CreatureAttacks are untouched.

`pipeline/spear-reference/build_private_crook_attacks.py` uses serialized field positions reported by the native reader, not runtime memory offsets. Its output is preparation only until crook-specific item binding is implemented. The new typed UDataTable.FindRow/AddRow APIs in installed83330635 provide reference access and native deep copying; verify BaseItemData row identity and write only private row copies if using that route.

Native weapon-frame fit is recorded in docs/native-spear-next/current-baselines/native-fit.json. It preserves the native Spear02 +Z shaft axis, matches cooked weapon Z bounds, and thickens only the cosmetic cross-section. The existing accepted root-rigid mesh remains unchanged. Source static-mesh ExtendedBounds are decoded, not its full render buffers. Native spear animations already provide camera/grip/jab placement; a fixed camera-space proxy is not the intended integration.
