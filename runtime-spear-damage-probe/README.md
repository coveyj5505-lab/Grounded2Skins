# Read-only native damage probe

This is a narrowly scoped follow-up to the already completed pose/mapping capture. It does not repeat animation extraction or jab recordings.

Copy `SpearDamageProbe` into the existing UE4SS `Mods` directory, add `SpearDamageProbe : 1` to the existing `mods.txt`, and disable/remove the previous `SpearReferenceProbe` entry. Load any character into a world and wait several seconds. No equipped weapon, target, attacks, camera switches, screenshot or new .usmap is needed.

Send the resulting `UE4SS.log` when convenient, then remove/disable this probe. Look for `[SpearDamageProbe] NATIVE_DAMAGE` and `COMPLETE`; a `STOP` reports a guarded failure rather than guessed damage.

It loads only the two attack tables already identified by the previous native capture, reads their row-name and three exported string columns, selects Player/Player2/Player3 and Spear/Spear2/Spear3, validates matching row counts and stable row ordering, and logs numeric damage fields. Missing optional combo rows are recorded as ROW_ABSENT. It never uses the variable-size GetDataTableRowFromName custom thunk, writes combat/inventory/save settings, equips an item, or applies the printed multiplier candidate.

Current native pose/animation evidence is already sufficient for carry/attachment investigation. This probe resolves only the missing damage-profile values. Five actual-Lua fixture groups pass, including one-shot behavior, menu/world transition, unexpected metadata, mismatched column sizes and incompatible charged profiles. Native Windows execution remains unverified.
