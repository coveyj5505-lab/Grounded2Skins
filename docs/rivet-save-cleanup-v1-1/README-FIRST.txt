RIVET SAVE / CHARACTER CLEANUP — v1.1 TEST PATCH

Game fully closed. Copy the included Mods folders into:
Augusta/Binaries/WinGDK/ue4ss/Mods/
Replace Rivet-Teleport and Rivet-BoPeep only. Do NOT nest Mods/Mods.
Keep mods.txt/mods.json, all Paks, UE4SS DLLs and other Rivet folders unchanged.
This patch is for the renamed final suite. Original final v1.0 ZIP is frozen.

TELEPORT V7
The native door inherits Maine.Switch.PersistenceComponent. Hiding and lifetime
limits did not prevent save restoration. Only the helper door we create gets:
 bNeverSpawnAsDynamicActor=true
 bShouldEditModeSave=false
The native persistence flag is checked/read back, and logged as PERSISTENCE.
Normal outpost doors, native map hold-Space travel and destination rules are
unchanged. The expected no-dynamic-restoration behavior requires Windows testing;
a lifespan or mock test is not proof of native save-system behavior.

BO PEEP V2.9
On every authoritative local pawn, before Willow-only auto-carry logic, check
for the exact private crook table AND RivetBoPeepCrook row. If inherited by a
non-Willow pawn after rejoin/character switching, remove that exact item and
log CHARACTER CLEANUP. Real ordinary spears are never removed by this check.
Willow still gets the crook automatically when both hands are empty; native
jabs, damage8 and spear reach are unchanged. Remote-client automation remains
pending, as in final v1.0.

COMBINED WINDOWS TEST
Use a save from before the unwanted doors appeared if available; keep a backup.
1. Load Buzz, leave/save, reload as Willow, then Woody, then Jessie, as before.
2. Each reload: check the previous logout location for a NEW floating door.
3. Use native map travel at least once, then logout/reload and check again.
4. Willow should receive her crook. Woody/Jessie should not inherit its wooden
   spear visual. An ordinary spear you deliberately equipped should remain.
5. Send UE4SS.log and tell us whether new doors appeared and whether the crook
   carried into other characters.

EXISTING SAVED DOORS
This patch does not delete unidentified historical doors. Their native owners
may no longer exist, making automatic removal hard to distinguish safely from
real world doors. It targets new helper persistence and inherited private items.
If you cannot use the earlier save, note the old doors' locations and distinguish
those from newly created ones during the test.

VALIDATION / ROLLBACK
24 Teleport + 13 crook lifecycle + 4 private-row local groups pass. They cover
native metadata checks, flag writes, ordinary destination behavior, character
cleanup, real-weapon preservation and previous visibility/rollback behavior.
Native save/reload and network behavior still need Windows confirmation.
Rollback by restoring the two matching folders from Rivet final v1.0, game closed.
