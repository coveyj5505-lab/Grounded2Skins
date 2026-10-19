NEXT DEVELOPMENT PHASE — BO PEEP REFINEMENT & SHEPHERD'S CROOK

Once you finish Woody's current character replacement build, immediately begin the next development phase for Bo Peep. Do not wait for another instruction from me.

We now have working Buzz, Bo Peep, and Jessie character replacements, with Woody being completed. Preserve all working character builds and avoid modifying the other characters unnecessarily.

## PHASE 1 — FIX BO PEEP'S EXISTING ISSUES

Bo Peep is already functioning in-game and looks mostly good, but two issues remain:

**1. Fingers and hands**
- Her fingers deform unnaturally during animations.
- Investigate bone mapping, rest-pose orientation, finger weights, and hand proportions.
- Correct the deformation without changing the rest of her appearance unnecessarily.
- Make sure her hands can support holding the crook naturally.

**2. Cape**
- Her cape deforms or behaves strangely during certain animations.
- Investigate its existing weights and how they interact with Willow's skeleton.
- Prioritize a stable, visually convincing cape during walking, running, sitting, and combat.
- A slightly stiff cape is preferable to one that stretches, twists, or clips excessively.
- Avoid complicated cloth simulation unless there's a compelling reason.

Keep the current playable Bo Peep build as a fallback.

## PHASE 2 — SHEPHERD'S CROOK AS HER DEFAULT WEAPON

I want Bo Peep's shepherd's crook to function visually as her signature melee weapon rather than having her punch enemies.

We already preserved the crook as separate geometry with its textures, weights, transform, and pivot. Reuse that asset.

**Important: I do NOT want to simply attach the crook to her hand and reuse punching animations.**

Grounded 2 already has spears and spear combat animations. Investigate how to reuse the game's existing spear animation system for Bo Peep.

### Normal movement — one-handed walking-stick pose

When Bo Peep is unarmed and not actively fighting:

- She should carry the crook casually in ONE hand, like a walking stick or shepherd's staff.
- The crook should be held relatively upright alongside her body.
- It should not be held horizontally across her chest or constantly pointed forward.
- It should not dominate the screen or obstruct the player's view.
- Her walking, running, and idle animations should remain natural.

The crook should feel like an accessory she casually carries, not a weapon she's permanently aiming.

### Combat — two-handed spear animation

When Bo Peep attacks while otherwise unarmed:

- Transition to an existing two-handed spear combat stance.
- Use the game's existing spear thrust/jab animations rather than punching animations.
- Position the crook so both hands grip it naturally during the attack.
- After combat, return to the relaxed one-handed walking-stick pose.
- Avoid unnatural snapping, floating hands, or excessive clipping where possible.

Ideally, reuse existing animation assets, animation layers, montages, or gameplay systems instead of authoring a completely new animation set.

### Equipment behavior

The crook is Bo Peep's default accessory only when she has no other equipment occupying her hands.

- Unarmed, no shield: crook visible.
- Attacking while unarmed: crook used with spear-style attacks.
- Equips another weapon: crook disappears.
- Equips a shield: crook disappears.
- Unequips weapons and shield: crook reappears.
- Sitting, interacting, or other special actions: hide or reposition it if necessary to avoid major clipping.

The crook should not replace the appearance of actual equipped weapons or interfere with their existing mechanics.

### Gameplay balance

For the first implementation, the crook should be cosmetic wherever possible.

Keep the game's normal unarmed damage, stamina costs, attack cooldowns, reach, hit detection, and other gameplay mechanics unless changing them is technically required.

We want the visual behavior of spear combat without giving Bo Peep an unfair or unintended weapon advantage.

## PHASE 3 — INVESTIGATE THE IMPLEMENTATION

Our current pipeline successfully replaces character meshes, but this feature may require more than a static mesh replacement.

Please investigate:

1. How Grounded 2 selects unarmed versus spear attack animations.
2. Whether Willow's animation blueprint can support switching between relaxed one-handed carrying and two-handed spear attacks.
3. How weapon and shield equipment states can control the crook's visibility.
4. Whether the crook can attach to an existing hand socket or bone.
5. How to preserve compatibility with our existing Bo Peep skin and the other three character mods.
6. Whether animation overrides, cooked asset replacements, or additional mod logic are needed.

Do not assume that simply attaching a crook to her hand will automatically trigger spear animations. Verify how the game actually handles these transitions.

Use the simplest reliable implementation available. If the full behavior is not feasible with our current modding tools, explain the specific technical limitation and implement the closest practical version without breaking existing gameplay.

## PHASE 4 — FUTURE GLIDING COMPATIBILITY

Eventually, we want Bo Peep's crook to transform into a parasol-style glider when she uses the dandelion tuft.

Do not implement that feature yet.

However, organize the crook geometry and attachment logic so we can reuse it for gliding later without rebuilding everything.

## DEVELOPMENT PRIORITIES

1. Finish Woody first.
2. Preserve stable backups of all working characters.
3. Fix Bo Peep's fingers and cape.
4. Investigate spear animations and equipment-state handling.
5. Implement the one-handed walking-stick carry pose.
6. Implement two-handed spear-style attacks.
7. Add weapon/shield visibility switching.
8. Package a new Bo Peep test build for Windows gameplay validation.

I care more about a working, recognizable, fun character than perfect animation polish.

Please continue through these phases autonomously where possible, using existing extracted game assets and our established tools. Only stop to request files, Windows-side tests, or decisions that genuinely require my involvement.