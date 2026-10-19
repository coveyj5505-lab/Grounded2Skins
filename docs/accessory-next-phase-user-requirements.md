NEXT PHASE — IMPLEMENT BO PEEP'S CROOK AND BUZZ'S WINGS

First-person compatibility is COMPLETE on all four Toy Story skins. Do not revisit it unless a new regression is discovered.

All four character replacements are working in-game. Preserve the current stable builds, including the head/body separation that fixed first-person visibility.

Now proceed with our accessory features.

## PHASE 1 — TARGETED UE4SS VALIDATION

Use the Grounded 2 SDK research you already completed.

We have identified these relevant functions and properties:

- MaineCharMovementComponent::IsGliding()
- GetGlidingStyle()
- EquipmentComponent main-hand/off-hand occupancy and GetItemInSlot()
- Relevant equipment stance and attack montage references

Verify the necessary reflected functions against our installed Grounded 2 build.

Use our existing working UE4SS v3.0.1 Beta installation.

Do not repeat broad player scans, SDK research, first-person testing, or completed experiments.

Prepare ONE small, targeted Windows test if necessary.

For gliding, test our reusable tuft trinket and confirm the state transitions from not gliding to gliding and back.

For equipment, distinguish between completely empty hands, main-hand equipment, off-hand equipment, and both hands occupied.

Once the necessary states are confirmed, proceed directly to implementation.

## PHASE 2 — BO PEEP'S SHEPHERD'S CROOK

This is our first accessory priority.

We already have the original crook geometry preserved separately in Blender.

Desired behavior:

**Normal movement**
- Bo Peep carries her crook upright in ONE hand, like a walking stick.
- It should rest alongside her body, not extend horizontally across the screen.
- Walking, running, and idle animations should remain natural.
- It should not obstruct first-person gameplay.

**Equipment**
- Both hands empty: crook visible.
- Any weapon or other item in the main hand: crook hidden.
- Any shield, torch, or other item in the off-hand: crook hidden.
- Both hands occupied: crook hidden.
- Both hands empty again: crook reappears.

Use an independent cosmetic attachment if possible. Do not equip a real spear or change the player's actual inventory.

**Combat**
I want Bo Peep to use two-handed spear-style thrust animations when attacking with the crook, rather than visually punching.

However, we must preserve normal unarmed damage, stamina, attack timing, hit detection, and reach.

Investigate the actual spear attack montage and stance assets before changing anything.

If safe animation substitution is not yet possible, implement the one-handed crook and equipment visibility first, then continue researching the attack animation separately.

Do not compromise gameplay mechanics just to achieve the visual effect.

**Special actions**
Hide or reposition the crook when necessary for sitting, climbing, swimming, or other interactions.

Keep the original Bo Peep model and current working build unchanged until the new accessory is tested successfully.

## PHASE 3 — BUZZ LIGHTYEAR'S WINGS

After establishing a reliable cosmetic attachment and state-detection approach, begin Buzz's wings.

We already preserved all six original wing panels in the Blender source.

Desired behavior:

- Walking/running/idle: wings retracted against Buzz's backpack.
- Gliding: wings extend automatically.
- Landing: wings retract.
- Use Grounded 2's existing gliding mechanics and physics.
- Eventually hide the dandelion tuft visual while Buzz's wings are deployed.

Prioritize a simple, reliable deployment effect over complicated animation.

If necessary, start with two visual states: retracted wings and extended wings.

We can add smooth deployment animation later.

Do not alter Buzz's existing body rig, first-person fix, or working character model unnecessarily.

## PHASE 4 — FUTURE BO PEEP GLIDER

Eventually, Bo Peep's crook should transform into a parasol-style glider.

Do not implement that yet.

Preserve compatibility with the crook attachment system so the glide-state detection developed for Buzz can be reused.

## WORKFLOW

Please work autonomously and efficiently.

1. Preserve backups of the four working character mods.
2. Validate only the required runtime functions.
3. Implement the simplest working Bo Peep crook attachment.
4. Add equipment-dependent visibility.
5. Investigate safe spear-style attack animation substitution.
6. Implement Buzz's glide-triggered wings.
7. Package test builds and provide clear Windows installation instructions.

Do not stop after every research discovery to ask whether you should continue.

Only request my involvement when you need a Windows-side test, missing game data, or a decision that materially affects implementation.

Avoid building unnecessary diagnostic frameworks.

The goal is to get these accessories functioning in-game, not to endlessly investigate theoretical possibilities.

Please begin now with the targeted glide/equipment validation and proceed into Bo Peep's crook implementation.