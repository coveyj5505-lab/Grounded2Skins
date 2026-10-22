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
