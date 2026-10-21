# Targeted UE5.7 loader repair test

The latest supplied log identifies v3.0.1 Beta ca6f9b4c, UE5.7 and Game Pass 0.320.7493.0. It terminates with `Was unable to find AOB for 'StaticConstructObject' via Lua script`; no accessory Lua startup is present.

UE4SS v3.0.1 `UE4SS/src/Signatures.cpp`, lines 196–215, installs a scan override only when `UE4SS_Signatures/StaticConstructObject.lua` exists in its working directory. The error above comes from that override's failed scan. This establishes an active failing override, not which bytes that user file contains. Renaming it is reversible and permits the built-in scan to run. Do not substitute a signature from another game or reuse a guessed address.

The official experimental-latest release notes explicitly add UE5.7 support. Downloaded asset: UE4SS_v3.0.1-1181-g83330635.zip. The test ZIP contains its unmodified AMD64 proxy and loader DLL, original license, and only our new wing configuration. It excludes settings, mods.txt, Paks and stock mod folders. Existing settings and Lua mods stay in place. The official release notes permit replacing the DLL in an existing installation. Current-game initialization still requires Windows confirmation.

## Manual drag/drop

1. Close the game. Back up `WinGDK/dwmapi.dll` and `WinGDK/ue4ss/UE4SS.dll` outside the game folder.
2. Rename `WinGDK/ue4ss/UE4SS_Signatures/StaticConstructObject.lua` to `StaticConstructObject.lua.disabled`. If this exact file is absent, report that rather than deleting other signature files.
3. Copy the downloaded ZIP's `WinGDK` contents into the game's existing `Augusta/Binaries/WinGDK`, merging folders and replacing the matching files. Do not create a nested WinGDK directory. Keep existing settings, mod folders and mods.txt entries.
4. Launch once. A new UE4SS.log should report the new loader rather than ca6f9b4c. If initialization still fails, send the new log plus the disabled signature file and UE4SS-settings.ini; no glide/equipment sequence is necessary.
5. If the crook/wing startup messages appear, check empty-handed Willow and press N as Max. Then test a real glide and landing. Manual preference OR gliding determines wing extension; toggling N during flight must not retract wings.

Rollback: close game and restore both original DLLs, the original wing_config.lua from the previous accessory package, and the signature file's original name. All released asset ZIPs remain unchanged.

## Sources

- https://github.com/UE4SS-RE/RE-UE4SS/blob/v3.0.1/UE4SS/src/Signatures.cpp#L196
- https://github.com/UE4SS-RE/RE-UE4SS/blob/main/docs/guides/fixing-compatibility-problems.md
- https://github.com/UE4SS-RE/RE-UE4SS/releases/tag/experimental-latest

The update is a targeted candidate, not a claim that the installed Grounded2 executable has passed its scans. DLL checks and Lua fixtures cannot replace that check.
