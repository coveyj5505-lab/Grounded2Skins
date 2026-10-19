ToyStoryDiscoveryV4: F9 only, movement/equipment component snapshots

WHY ANOTHER VERSION
User's V3 log recorded all7 snapshots (45 scalar values each) with no errors. Only jump counters changed in the glide snapshot; they do not establish gliding. Equipment states were not exposed by the captured player fields. Actual runtime ObjectProperty metadata exposed /Script/Maine.SurvivalCharacter:CharMovementComponent and EquipmentComponent. V4 follows exactly those two references and reads only metadata-declared Bool/Byte/Int/Int64/Float/Double fields on them. It never reads other object values, arrays, structs, maps, delegates, item containers or guessed field names. EnumProperty wrappers are not decoded. No function hooks, gameplay writes, animations, attachments, item changes or save edits. Cache holds descriptor strings only; component instances are reacquired per snapshot.

INSTALL
Close game. Move all old ToyStoryDiscovery/V2/V3 folders outside ue4ss/Mods and remove their mods.txt entries if added. Copy ToyStoryDiscoveryV4 into ue4ss/Mods. enabled.txt is included; if mods.txt is required, append ToyStoryDiscoveryV4 : 1, preserving everything else. Keep working UE4SS, FreeBuild and skin files unchanged.

ONE SESSION, SAME REUSABLE TUFT TRINKET IS FINE
Use a copied test save and a safe drop. F9 ALONE, no Ctrl.
1. Standing, fully unarmed with NO SHIELD: F9. Wait5seconds. First snapshot does bounded component discovery; stop if crash/freeze/error.
2. If responsive, deploy the tuft trinket glider and press F9 while visibly gliding.
3. Standing after landing, still unarmed: F9.
4. Spear ONLY, no shield: F9.
5. Spear AND shield: F9.
6. ONLY shield, no weapon: F9.
7. Fully unarmed again, NO shield: F9.
Keep roughly3-5seconds between captures. Optional normal airborne jump WITHOUT gliding and/or spear attack snapshots help distinguish states; note the order if included. You may use sword for an additional weapon snapshot, but spear/shield/unarmed are the primary comparisons. This version takes snapshots, not continuous recording. Send UE4SS.log before restarting, plus snapshot order. Do not consume a regular tuft merely to repeat this test; the trinket glide is the target for now.

LIMITS
New component reference/scalar reads are Windows-UNTESTED; native UE4SS access violations cannot be contained by Lua pcall. Offline tests do not prove native safety. Each native call has BEFORE/AFTER logs. This is intended to locate state, not implement crook/wings or guarantee another test will not be needed. Components may store equipment in complex properties; V4 deliberately logs only that metadata. The first128 matching scalars and first512 descriptors per class are bounded; no arbitrary object graph scan is performed.

REMOVE: close game, move folder outside Mods; remove only its mods.txt entry if added.
