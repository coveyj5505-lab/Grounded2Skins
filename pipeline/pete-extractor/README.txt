PETE DISCOVERY + TARGETED ORIGINAL ASSET EXTRACTION (READ-ONLY)

Use the same Windows retoc.exe 0.1.5 and Python 3.11+ as Willow/Hoops.

1. Extract this ZIP to a normal folder.
2. Double-click Start-Extraction.cmd.
3. Choose retoc.exe and ORIGINAL Augusta-WinGDK.utoc with adjacent UCAS.
4. Upload the Desktop Grounded2-Pete-[timestamp].zip.

The helper discovers actual indexed SK mesh filenames under the expected
/Game/_Augusta/Art/Characters/Player_Male02 directory, including hair, then
follows their actual skeleton/physics imports. This directory/character identity
and its bone/LOD layouts must be checked against the extracted data; no guessed
SK_Male_Teen_02 filename, Max skeleton or copied bind table is assumed valid.

No full-game copy, texture dump, game injection or installation changes.
Only selected packages are read; capped at48packages/128MiB decoded.
Reports include paths, classes, hashes, imports and unchanged source size/mtime.
An incomplete extraction still produces a ZIP; upload the available data/report
rather than repeating it. source-index.log remains locally for diagnosis.

Driver control tests use the known Commander101 container: an explicit Male01
selection extracts known meshes/dependencies and reports missing original
skeletons correctly; default Male02 finds zero meshes. These controls verify
selection and extraction, NOT actual Pete paths or stock skeleton compatibility.
The Windows GUI derives from the launchers you already used successfully; its
GUI cannot be run in the Linux preparation environment.
