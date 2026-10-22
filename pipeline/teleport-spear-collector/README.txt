CURRENT TELEPORT + SPEAR BASELINE COLLECTOR — READ ONLY

Close Grounded 2, leave the failing Teleport trio removed, and double-click
Start-Collection.cmd. Select the same Windows retoc.exe 0.1.5 used previously,
then the UPDATED game's ORIGINAL Content/Paks/Augusta-WinGDK.utoc.
Python 3.11+ is required, as in the previous collectors.

Upload ONE Grounded2-NativeBaselines-....zip from your Desktop. Partial output
is useful. No game launch, UE4SS changes, targets or attack recordings needed.
This does not install anything, update mods, or modify game files/saves.

WHY THIS IS DIFFERENT:
The successful damage probe already gave the numerical values (unarmed8,
spear20/48/54). The previous animation assets and .usmap are also sufficient
and are NOT collected again here. We now need the current cooked baseline
packages to compare the old Teleport controller/map against the actual game,
and the original attack tables/Spear02 mesh to prepare the native crook using
correct serialization and weapon geometry. A container-only repair still
crashed on startup; packaging verification alone did not establish compatibility.

Exactly eight known package paths are selected. No recursive asset traversal,
full container copy, textures, character skins, or broad data dump. Maximum
64 MiB decoded. The source index is read to locate packages; the successful
upload ZIP omits that broad index. The report records hashes, paths, missing
packages, source metadata checks and partial errors.
