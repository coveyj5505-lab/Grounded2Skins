GROUNDed 2: ORIGINAL MAX COMPATIBILITY CHECK (read-only)

This helper extracts FIVE original packages and their own bulk chunks. It does
not unpack/copy the full 35.5 GB archive, modify installed mods, change game files,
inject into the game, or require the game to run.

Requirements:
- Python 3.11 or newer (python.org).
- Windows retoc.exe reporting retoc_cli 0.1.5.
  Releases/source: https://github.com/trumank/retoc/releases
  The tested source commit is 885a8dae740cb1ce1e41ff2e74f67f9f0c118237.
  Do not download a DLL from an unrelated site. Retoc's loader verifies its Oodle
  dependency; the Python helper also checks any existing known decoder library.

1. Extract this helper ZIP to a normal folder, keeping all its files together.
2. Double-click Start-Extraction.cmd. Select retoc.exe, then the ORIGINAL game's
   Augusta-WinGDK.utoc. Its adjacent Augusta-WinGDK.ucas must be present.
3. A Grounded2-StockMax-[timestamp].zip is created on your Desktop. Share that ZIP
   for the bone/pose/material/physics comparison. Do NOT upload the full UCAS.

The launcher uses a process-local PowerShell execution-policy option to run this
readable local script; it does not change machine policy. No legacy conversion or
Paks-folder context is requested, so installed Commander101/Buzz overrides cannot
silently substitute for the original game assets during this extraction.

The five package paths are listed in targets.json: stock Max body mesh, backpack
mesh, USkeleton, stock skeletal PhysicsAsset, and Max's Apparel01 material instance.
The first three answer the bone/rest-pose question. The other two allow inspecting
skeletal physics differences and the actual atlas material dependency.

On failure, keep the Desktop output/logs. A missing target or nonzero retoc exit
stops the operation; an incomplete ZIP is not presented as success. The wrapper
has not been executed on Windows in the cloud environment. Its underlying Python
extractor has been exercised against the supplied mod using the same retoc CLI;
actual original-game extraction remains a Windows step.

Correction 2026-10-18: the stock meshes import /Game/Art/Characters/Player_Male01/Mesh/SK_Male_Kid_01_PhysicsAsset.
The former _Augusta/.../SK_Male_Teen_01_w_BackPack_PhysicsAsset path belongs
to the Commander101 replacement and was absent from the original container.
