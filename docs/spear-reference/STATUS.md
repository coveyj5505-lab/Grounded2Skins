# Native spear crook: targeted reference probe

## Current user requirement

Reuse the native spear grip, carry and attack animations, reach and hit detection. The user first selected native spear gameplay, then explicitly retained **unarmed-level damage**. Treat that clarification as controlling: native spear reach is now authorized, damage must be matched to unarmed. Do not silently retain the earlier unarmed-reach restriction or ship full native spear damage. Existing accepted skins remain frozen.

## Missing evidence this probe supplies

- Actual reference spear visual actor/primitive and mesh asset paths, attachment parent/socket, native local mesh bounds when supported, and world transforms.
- Camera transform/scale/FOV/viewport and native hand transforms through FP/TP rest and thrust. This replaces guessed camera offsets.
- Current native montage, position and stance where reflected getters/properties permit.
- Equipped item's attack row handles/ranges, native damage modifier/custom multiplier; character default/current attack rows/ranges and default unarmed base damage when the native UI helper is available.
- Network authority flag for deciding where a damage override must execute. A client-only visual replacement must not be mistaken for an authoritative damage change.
- Current native type-layout .usmap, using the builtin DumpUSMAP(false) verified against exact installed UE4SS83330635 source. Existing16 animation packages are already collected; do not extract them again.

No native gameplay setters, animation playback, cosmetic changes, equipment changes, actor movement or hooks. Collection runs on the game thread, is bounded to600 frames/2400 active polls, and starts only after an actual main-hand item is equipped. A map-generation failure or optional getter failure leaves other read-only collection available.13 mocked-Lua groups pass; Windows native API acceptance remains unverified.

## Development route after collection

Use the native spear presentation/attack driver instead of a camera-mounted crook rotating beside punching arms. Fit the crook's wrapped grip and thicker shaft to the measured native spear frame, preserving its hook. Verify native damage source and unarmed baseline before implementing a scoped damage override; do not guess a constant or globally modify all spears/characters. Maintain accepted skins and persistent view lifecycle. Determine inventory/automatic empty-hand integration from the actual native attack and attachment data rather than silently equipping an item or writing saves.

The actual spear geometry may require an additional small exact-asset extraction if local bounds/poses are insufficient for diameter matching. Do not request another broad character or animation collection. The unpublished cosmetic V2 draft is not the native spear implementation and remains unshipped.
