ToyStoryAccessoryCheck v2.0 - NO Reflection() binding poisoning
Read-only targeted equipment, spear montage/stance and reusable-trinket glide recording.
First-person and all skins remain unchanged; no FP test requested.

INSTALL WITH GAME CLOSED
Remove ToyStoryObjectAccess and old ToyStoryDiscovery* from ue4ss/Mods and their mods.txt entries if present. Replace the old ToyStoryAccessoryCheck folder with this folder. enabled.txt included; keep/add ToyStoryAccessoryCheck : 1 only if your loader needs mods.txt. Keep working UE4SS/FreeBuild/skins untouched. Restart the game: an already-poisoned per-mod Lua binding cannot be repaired by changing the accessor spelling.

FIRST FIVE SECONDS - CHECK READY BEFORE SPENDING TIME ON GAMEPLAY
Load a save standing with both hands empty, then press F9 ONCE.
Wait5seconds. Open ue4ss/Mods/ToyStoryAccessoryCheck/Scripts/AccessoryCheck-status.txt.
- READY: equipment AND glide getter values are valid. Proceed below.
- PARTIAL READY: EQUIPMENT ONLY: do the equipment/attack sequence only; no glide needed. Equipment/crook progress continues independently.
- PARTIAL READY: GLIDE ONLY: do glide/land only; equipment recording isn't ready.
- STOP, NOT STARTED, or missing status file: preserve/send UE4SS.log; don't repeat a long gameplay sequence. Readiness also prints in UE4SS.log if folder permissions prevent writing the status file.
No extra keypresses are needed while gliding. You can alt-tab to read the small status file, then return to the same running session.

ONE RECORDING SESSION (automatic180seconds from F9;0.5second sampling)
1. Empty BOTH hands/no shield.
2. Spear only:2normal attacks and a charged attack.
3. Spear+shield: same attack sequence if convenient.
4. Shield only.
5. Empty BOTH hands again.
6. If glide READY: ordinary jump without tuft (optional), then glide with your reusable TUFT TRINKET and land.
Hold equipment states about3seconds. F9again stops early, otherwise recording ends after3minutes. Send UE4SS.log BEFORE relaunching, plus changed action order/skipped actions. Short attacks may fall between samples; charging and montage fields are passive observations, not attack execution. No first-person or four-character repeat needed.

WHY THIS FIX IS DIFFERENT
The short type diagnostic confirmed both component access forms returned RemoteObjectBase, while pawn was AActor and descriptors were ObjectProperty. Exact Beta ca6f9b4c source reveals Reflection() can create a bare 'UObject' metatable before the full UObject constructor. Later reads reuse it and lack GetClass/IsA/GetFullName. v2.0 never calls Reflection(): exact known field descriptors come from native UClass.ForEachProperty metadata (the V2-proven class path), then ordinary indexing constructs full UObject wrappers. Actual wrapper tags are checked; RemoteObjectBase is rejected without calling missing methods. No pointer casting, raw addresses, engine/SDK offsets, metatable patches, DLL changes or blanket unwrapping.

RESILIENCE
Each optional getter/property/enum has its own protected Lua operation. One error disables that operation and leaves equipment, glide and passive attack collection independent. Native access violations are NOT catchable by Lua. The new binding workaround/getters still need actual Windows confirmation; offline mocks don't establish native safety. No new rendering/visibility/camera/inventory/animation/combat/movement changes. No crook or wing actors spawned by this test.

REMOVE
Close game, move this folder outside Mods and remove only its mods.txt entry if added. Stable skins remain untouched.
