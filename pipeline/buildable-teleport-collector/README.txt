BUILDABLE TELEPORT — CONSTRUCTION CATALOG FOLLOW-UP (READ ONLY)

The first trail-marker collection succeeded. This follow-up answers the new
build-menu question: is there already a teleporter recipe/build entry, and what
native types handle registration? It does not repeat the five map/teleporter
baseline packages except if one is reached by a relevant indexed import.

1. Close Grounded 2. Extract this entire ZIP into a new folder.
2. Double-click Start-Collection.cmd.
3. Choose your existing Windows retoc.exe 0.1.5.
4. Choose ORIGINAL Augusta-WinGDK.pak OR Augusta-WinGDK.utoc in Content/Paks.
   Matching Augusta-WinGDK.utoc and .ucas must be beside it.
5. Upload ONE Grounded2-BuildableTeleport-....zip from your Desktop.

Python 3.11+ is required, as before. No game launch, UE4SS install, save copy,
test building, or gameplay sequence is needed.

Reads the actual Table_AllBuildings construction catalog, relevant indexed
construction recipe/UI/placement assets, and teleporter/trail-marker logic
variants. It follows only imports matching those logic/catalog categories.
The native Engine.Actor parent alone does not tell us whether a hidden catalog
entry already makes the teleporter placeable. That is what we are checking.

Includes the adjacent global.utoc/global.ucas type-metadata pair ONLY when both
are present and their COMBINED size is at most 16 MiB. These resolve native
class/function names, not models or textures. A missing/oversize pair is reported;
the independent construction extraction still runs. Do not download substitutes.

Limits: 32 selected logic/table packages and 64 MiB decoded, plus the global pair
up to 16 MiB. No mesh, image, sound, save or associated art bulk payloads. The full
archive index stays local. Nothing is installed or modified in game folders,
mods, or saves. Reports, selected chunks, bounded global metadata and extraction
logs go into the Desktop ZIP. Partial results are useful.

EXTRACTED_READ_ONLY means bytes were collected, not that building or fast travel
is implemented. Some table properties may still need matching mappings or runtime
metadata; this collector cannot guarantee an entirely offline implementation.
