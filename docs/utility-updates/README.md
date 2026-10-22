# Utility mods — UE5.7.4 test candidates

**Latest Windows result:** FreeBuild and InvisibleArmor Lua are user-confirmed working. The Teleport trio in the V1 ZIP is withdrawn after a startup crash. Keep it removed; the older installation/testing steps below are historical candidate instructions, not a recommendation to reinstall it. Current native Blueprint baselines are being collected for a substantive repair.

Prepared for Grounded 2 release 0.6.0.3. These are locally validated candidates, not Windows-confirmed releases. Accepted character packages and all previous releases are unchanged.

## Install manually

Close the game. Keep backups outside the game's Paks directory.

1. Remove the old Invisible Armor and Teleport trios from Paks: `zInvisibleArmor_P.*` and `Xingxing_OutpostMapTeleport_905_P.*` (each `.pak`, `.utoc`, `.ucas`). Remove any earlier duplicate of these mods too.
2. Copy `UE4SS/Mods/FreeBuild` and `UE4SS/Mods/InvisibleArmor` from the ZIP into your existing UE4SS `Mods` folder. Replace the old **FreeBuild script folder**, rather than keeping two FreeBuild versions.
3. Add or update these lines in the existing `mods.txt`, preserving all other mod entries:
   ```
   FreeBuild : 1
   InvisibleArmor : 1
   ```
4. Copy all three files from `Paks` into your normal mod Paks folder **when testing Teleport**. Do not install `global.utoc`/`global.ucas`; none are included.

There is no installer or new keybind. The Lua mods require the already working UE4SS installation. FreeBuild must run on the host for authoritative building settings; Invisible Armor runs on each client that wants the appearance hidden.

## What changed

- **FreeBuild:** preserves the supplied script's building autocomplete behavior. Calls now run on the game thread; native class/function/property metadata and host authority are checked before changing `bAutoCompleteBuildings`. It does **not** enable free crafting, unlock recipes, or change inventory. The original script only set this one building flag as well.
- **Invisible Armor:** replaces the old 146-mesh cooked override with Lua that hides only player head/chest/arms/legs **armor render components**. Armor remains equipped with its normal stats. Character replacement meshes, hair and wrist device are not deliberately hidden. Visibility is rechecked after equipment changes.
- **Teleport:** repairs the archive's mismatched IoStore container identity. Its two original controller/map Blueprint chunks are byte-identical; their behavior and controls have not been redesigned. Both now deserialize with the supplied current-build mappings. This establishes readable packaging, not full Blueprint/gameplay compatibility. If an obsolete Blueprint call remains, this candidate may still fail in Windows.

## Test in this order

1. Start with the two Lua folders and **without Teleport's trio**. Load the host world, place a cheap building blueprint, and check autocomplete. Verify crafting still behaves normally.
2. Equip/remove armor on any accepted character, change FP/TP several times, then leave and rejoin. Check armor is invisible, the skin remains, and normal armor stats persist. Other players need their own InvisibleArmor Lua installation to hide armor on their screen.
3. Exit fully, add Teleport's repaired trio, and relaunch. Check menu, world load, map open/close, and the mod's existing teleport controls. Then leave/rejoin and exit. The original Blueprint includes map teleport/PTS handlers and a Shift+U binding; no new controls are introduced here.

The two Lua scripts print `[FreeBuild UE57]` and `[InvisibleArmor UE57]` with `ACTIVE`, `WAIT`, or `SCHEMA REJECTED` evidence. A rejected schema deliberately leaves the setting/component alone. Teleport is a Pak mod and does not produce these Lua prefixes. Retain the latest UE4SS log after a test.

Rollback: close the game, remove the two new Lua folders/entries and Teleport's repaired trio, and restart. No save edits are performed by the update scripts; native building actions can still persist completed buildings normally.

## Local validation

Seven actual-Lua fixture groups cover host/client behavior, menu/rejoin, unexpected metadata, repeated setting application, equipment refresh, and leaving body/SCAB untouched. They do not simulate Unreal rendering or networking.

Teleport passed retoc verification, exact staged/re-extracted chunk hashes, matching TOC/header/header-key identity, preserved asset paths, and current UE5.7 package deserialization for both assets. Original input receipts and compact validation are in this directory.
