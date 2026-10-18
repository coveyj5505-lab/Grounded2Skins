# Extract selected Grounded 2 packages locally

This helper reads `Augusta-WinGDK.utoc` and seeks into the adjacent
`Augusta-WinGDK.ucas`. The UCAS alone is insufficient: its matching UTOC is required.
It reads the archive index, then extracts only the ten requested packages in
`targets.json`, plus associated bulk-data chunks. It does not unpack/copy the
35.5 GB archive or modify game files. Output must be a new directory outside Paks.

Requirements: Python 3.11+ and the Windows retoc 0.1.5 CLI from
https://github.com/trumank/retoc/releases (or build the pinned source commit
885a8dae740cb1ce1e41ff2e74f67f9f0c118237). Verify the release checksum. Existing
Oodle libraries next to retoc are checked against pinned 2.9.10 hashes. When absent,
retoc's own loader downloads its checksum-verified library; keep TLS verification.

From PowerShell, in this helper directory, edit the Paks and retoc paths:

```powershell
$Paks = 'D:\YourGameFolder\Augusta\Content\Paks'
.\Extract-Selected.ps1 -Retoc 'C:\Tools\retoc.exe' `
  -Utoc (Join-Path $Paks 'Augusta-WinGDK.utoc') `
  -Output "$env:USERPROFILE\Desktop\Grounded2-selected-assets" `
  -LegacyContext $Paks
```

`-LegacyContext` additionally converts only these packages to legacy
`.uasset/.uexp/.ubulk` using the global metadata already in Paks. It rejects selected
paths duplicated/overridden by another container, and checks actual converted
counts instead of trusting retoc's exit code. If context conversion fails, the
selected raw chunks already extracted can still be useful; retain the logs.

Equivalent Python command (all paths are supplied as arguments, not shell code):

```powershell
py -3 .\extract_selected.py --retoc 'C:\Tools\retoc.exe' `
  --utoc (Join-Path $Paks 'Augusta-WinGDK.utoc') `
  --output "$env:USERPROFILE\Desktop\Grounded2-selected-assets" `
  --legacy-context $Paks
```

Omit the last option for raw Zen extraction only. The resulting `chunks/` files
are raw cooked chunks, not Blender files or a standalone installable mod.
`extraction-report.json` associates every chunk with its path and SHA-256. When
Python's optional `blake3` module is already installed, it also compares each
selected payload with its original TOC content hash. Otherwise that verification
is explicitly recorded as unperformed; SHA-256 is still recorded for transfer.
No whole-archive verification reads through the 35.5 GB file.

Upload the resulting `legacy/` directory (or `chunks/` plus
`extraction-report.json`) and logs, rather than the full game UCAS. Split any
upload exceeding the session's 32 MiB per-file transfer limit. A missing target is
reported explicitly; it may reside in another original game container, so do not
substitute a similarly named package.

The core Python helper was actually tested here against Commander101: two selected
packages and one associated bulk chunk (38,132,038 bytes), two legacy conversions,
and no source size/mtime changes. Extracted chunk SHA-256 values were also compared
with the independently decoded originals. Windows PowerShell and the 35.5 GB game
archive are unavailable in this cloud host; that wrapper/archive run remains untested.

These exports do not provide a `.usmap`: property mappings are separate runtime
reflection/schema data. The known next CUE4Parse blocker is a matching Grounded 2
mapping file, not the global container, which has now been supplied and decoded.
