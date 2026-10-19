ToyStoryAccessoryCheck - ONE READ-ONLY focused SDK check
First-person functionality is COMPLETE. Do not replace skins, repeat FPtests, or install any unpublished FPoverride. This package has NO cooked assets and NO visibility changes.

INSTALL
Close game. Move old ToyStoryDiscovery/V2/V3/V4 folders outside ue4ss/Mods and remove their mods.txt entries if present. Copy ToyStoryAccessoryCheck to ue4ss/Mods. enabled.txt is included. If your loader requires mods.txt, add ToyStoryAccessoryCheck : 1 without replacing other lines. Keep existing UE4SS3.0.1Beta, FreeBuild, four stable skins and head/body separation unchanged.

ONE SESSION - PRESS F9 ONCE, THEN PLAY; NO CAPTURE KEY WHILE GLIDING
Load a copied test save. Use whichever working character is convenient; state-getter validation does not need all four characters. Start standing, with NO weapon or shield.
Press F9 once, wait5seconds. If still responsive, do the following within3minutes, holding equipment states for about3seconds:
1. Empty hands, no shield.
2. Spear ONLY (no shield); perform2normal spear thrusts if convenient.
3. Spear+shield.
4. Shield ONLY (no main-hand item).
5. Empty BOTH hands again.
6. Ordinary jump WITHOUT gliding (optional comparison), then glide with your existing REUSABLE TUFT TRINKET and land.
Press F9 again to stop, or it stops after3minutes. Do not press Ctrl or any key while gliding to capture; sampling is automatic every0.5seconds. No camera-toggle/first-person test needed. Keep the order above or note differences.

Return ue4ss/UE4SS.log before relaunching. Tell us if you skipped spear attacks or used a different state order. This automatically captures getter transitions, hand-item names, stance values and (when sampled during an actual attack) its montage reference. Very short attacks might fall between samples; a missing montage would not prove that no attack occurred.

WHAT IT DOES
Looks up a short allowlist of exact reflected SDK functions. Checks input/return property-name/kind signatures and receiver class before invoking getters. Reads only whitelisted ObjectProperty component references and BoolProperty fields. Equipment slot numbers come from the LIVE EEquipmentSlot enum; no SDK memory offsets or assumed slot integers. Missing/mismatched signatures are logged and skipped. Logs native-call BEFORE/AFTER markers and state changes. GetIsFirstPerson is a read only for future accessory suppression; no FPtesting or changes requested.

WHAT IT DOES NOT DO
No general player properties, recursive object dump, component traversal, mesh/material/camera writes, hooks, attack calls, animation replacement, inventory edits, movement/physics changes, crook/wings spawning or save writes.

LIMITS
New getter calls are not yet Windows-tested. Offline Lua tests cannot establish native safety; Lua pcall cannot catch native access violations. Stop if crash/freeze, preserve UE4SS.log before restarting, and remove this mod. Header/signature matching is a compatibility guard, not proof of correct runtime behavior. Existing V3 succeeded but did not directly measure the needed component states; no V4 results have been supplied.

REMOVE
Close game, move ToyStoryAccessoryCheck outside Mods, and remove only its mods.txt entry if added. Stable character mods remain unchanged.
