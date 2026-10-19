HOOPS DISCOVERY + TARGETED ORIGINAL ASSET EXTRACTION (READ-ONLY)

Use the same Windows retoc.exe0.1.5 and Python3.11+ as the Max extractor.

1. Extract this helper ZIP to a normal folder.
2. Double-click Start-Extraction.cmd.
3. Choose retoc.exe, then ORIGINAL Augusta-WinGDK.utoc with its adjacent UCAS.
4. Upload the new Grounded2-Hoops-[timestamp].zip created on your Desktop.

The helper scans the actual game index. It discovers SK meshes under
/Game/_Augusta/Art/Characters/Player_Female02, including hair variants, and reads
those packages' real Zen imports to select the skeleton and physics dependencies.
No guessed SK_Female filename, assumed bone count, Max skeleton substitution,
texture dump, full35GB extraction, game injection or game-file modification.

The report records actual paths, export classes, imports, extracted chunk hashes
and unchanged input size/mtime. Extraction is capped at48packages/128MiB decoded.
It never overwrites an existing output directory. Only selected chunks are read.
The launcher uses a process-local execution-policy option, not a machine change.
No additional DLLs from random download sites are required.

If a dependency is absent or a header differs, the ZIP still includes available
chunks and an explicit partial report. Upload that ZIP; do not repeat extraction.
source-index.log remains locally for diagnosis; it is not bundled into the ZIP.

The underlying extraction driver has been exercised on Linux against the known
SuperEvie reference as a positive discovery/partial-dependency control and the
Commander101 reference as a negative Hoops-directory control. That is not evidence of Hoops's actual paths
or bone count. The Windows dialog wrapper is derived from your working Max
extractor; its GUI cannot be run in this Linux environment.
