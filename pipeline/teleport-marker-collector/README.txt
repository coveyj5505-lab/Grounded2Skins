TRAIL MARKER / NATIVE TELEPORT COLLECTOR — READ ONLY

1. Close Grounded 2. Extract this entire collector ZIP into a new folder.
2. Double-click Start-Collection.cmd.
3. Select your existing Windows retoc.exe 0.1.5.
4. Select ORIGINAL Augusta-WinGDK.pak OR Augusta-WinGDK.utoc in Content/Paks.
   The matching Augusta-WinGDK.utoc and .ucas must be beside it. A PAK alone
   cannot provide the cooked Blueprint assets.
5. Upload ONE Grounded2-TrailMarker-....zip from your Desktop.

Python 3.11+ is required, as for the previous collectors. No new game launch,
UE4SS mod, trail-marker placement, save copy, or gameplay recording is needed.

This reads five exact map/controller/teleporter baselines, discovers marker
logic/UI paths from the actual index, and follows only marker logic imports.
It does NOT guess a trail-marker filename or unpack all game content.
Limits: 32 packages / 64 MiB decoded. Mesh, texture and bulk payloads are not
collected. The full source index stays local and is omitted from the ZIP.
Reports, selected raw package chunks and extraction logs are included.
Nothing is installed or changed in the game, mods, or saves.

Partial output is useful: missing paths, unsupported headers, tool errors and
budget limits are reported. EXTRACTED_READ_ONLY means selected bytes were
collected; it does not mean trail-marker travel works or is implemented.

Purpose: establish the current marker actor/UI types and native destination
requirements before deciding whether temporary arrival pods can provide safe
marker travel, particularly for joining multiplayer clients. No guessed RPC,
marker conversion, coordinate teleport, or persistent destination is included.
