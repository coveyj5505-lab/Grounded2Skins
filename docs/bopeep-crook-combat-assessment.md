# Deferred Bo Peep crook combat — spear animation plan

**Latest user direction supersedes the earlier stock-punch proposal: investigate reusing existing spear animations for the crook.** This remains future work after current character work/fixes. No spear, combat, equipment, Blueprint or gliding modification is implemented now.

## Desired presentation and preserved requirements

When Bo Peep is otherwise unarmed, show her preserved crook using a spear-like hold, carry and attack animation presentation. Hide it with any equipped weapon or shield, and during interactions with major clipping; restore it when eligible again. Keep original unarmed damage, timing and collision unless the user explicitly changes that earlier requirement. Coordinate future gliding so only the parasol/glider representation is visible while gliding, with no duplicate hand crook.

Use the existing spear visual/animation path as the first animation candidate instead of trying to make normal punches look like staff attacks. This can avoid authoring custom animations, but suitability of spear thrusts, hand spacing, crook length and curved tip still needs preview/testing. No promise that a particular spear montage/weapon definition already supports this behavior.

## Simplest investigation path

1. Locate the actual current-build spear held-item visual, carry/grip poses and attack montage/animation routing, using discovered game definitions rather than guessed Blueprint names.
2. Test a cosmetic crook visual in that existing spear presentation path. A reskin of an **actually equipped spear** is a useful animation/attachment control, but it does not by itself implement an unarmed-default crook or preserve unarmed gameplay.
3. Determine whether presentation can select those spear animations for Bo Peep's eligible unarmed state while retaining the original unarmed combat mechanics. Check all relevant animation notifies, trace events, combo transitions, montage durations, locomotion layers and interaction interruption behavior.
4. Add the smallest verified equipment/state controller for visibility and presentation routing, scoped to Bo Peep. No new animation system or automatic full combat replacement.

Simply equipping an invisible spear could also select spear statistics, reach, attack timing, damage traces, durability or inventory behavior. Do not treat that as a cosmetic implementation. Likewise, playing a spear montage may invoke attack notifies or mismatch the unarmed timing window. Existing spear animation reuse does **not** automatically guarantee unchanged unarmed gameplay. If these cannot be separated safely through existing game definitions, report the precise limitation before implementing broader changes.

## What the current skin pipeline supports

The current pipeline writes skeletal render buffers, fixed skin weights, textures/material references and IoStore metadata. It can produce the crook's render asset, but cannot by itself select spear animations for an unarmed actor, observe inventory, or conditionally hide it. A static hand-weighted addition would be always visible and would not satisfy the new spear-animation plan.

A separate cosmetic accessory is still a useful asset boundary for the future weapon-presentation system, with collision/physics/overlap/damage disabled. Stock Willow has verified hand bones `r_hand_JNT` (index147) and `l_hand_JNT` (53); actual spear attachment transform, sockets and two-hand IK must be inspected. The original source `e_stick` pivot is preserved as an authoring candidate, not a verified game spear socket. No shared game skeleton changes are needed just to author an attachment asset.

Equipment visibility requires existing game equipment logic, a compatible Blueprint/data-asset entry point, or a verified supported runtime hook. Animation routing may require an existing weapon/animation data override or animation-graph changes if no suitable selector exists. Prefer the smallest existing selector/data path, retaining the game's AnimBlueprint where feasible; do not assume a simple component toggle also handles the spear animation change. Adding a new Blueprint to a PAK does not make it run automatically. UE4SS/WinGDK compatibility, arbitrary UE5.6 Blueprint cooking and the needed game hooks are not verified by working skins.

## Accessory state policy

| State | Crook presentation |
| --- | --- |
| Bo Peep, otherwise unarmed, normal locomotion/combat | Eligible for crook + verified spear presentation |
| Any actual weapon or shield equipped | Hidden; preserve equipped item behavior |
| Sitting/climbing/swimming/interaction with major clipping | Hidden; defer to interaction animation |
| Gliding | Hide combat crook; future parasol owns presentation |
| Another character, death/respawn transition or unknown state | Hidden until eligibility is established |

Transitions must react to equipment changes, character swaps, respawns and interaction/glide changes, not only initial spawn. Future parasol and combat crook share one state policy to avoid conflicting animation ownership or two visible props.

## Current evidence and remaining unknowns

Verified: preserved separate crook geometry/UVs/material/source weights/transforms and source pivot; stock Willow hand bone names; working Bo Peep skin; no character/equipment logic override in the skin ZIP. Unverified: spear asset package paths, equipment/animation interfaces, montage notify semantics, game loading entry point, and whether unarmed mechanics can be retained with spear animation presentation. Inspect these later through exact discovered assets or supported tooling; do not request a full-game upload or install a runtime framework now.

The original Bo Peep source, playable body and current mods remain unchanged. The spear plan replaces the earlier recommendation to retain punches for the cosmetic crook; it does not imply that feature is already supported or tested.
