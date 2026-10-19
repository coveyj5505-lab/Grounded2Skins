WITHDRAWN: ToyStoryDiscovery V1 crashed in UE4SS when the user pressed Ctrl+F8.
Do not use the original V1 probe or repeat the gliding test.

Recovery:
1. Close Grounded 2.
2. Copy the existing UE4SS.log somewhere safe BEFORE relaunching; startup may replace it.
3. Move ToyStoryDiscovery entirely outside the UE4SS Mods directory.
4. If you added ToyStoryDiscovery : 1 to mods.txt, remove ONLY that entry.
5. Keep the working UE4SS installation, FreeBuild, and character skin packages unchanged.

Return UE4SS.log (from your existing UE4SS installation, commonly beside the Mods directory), or the last ~150 lines including [ToyStoryDiscovery]. Note whether you were in a loaded save or menu. The Augusta stack shows a native null read through UE4SS but does not identify the failing API. Lua pcall does not catch native access violations. No claim of safe runtime reflection can be made from offline Lua mock tests.

This replacement main.lua is a quarantine stub. It only prints that discovery is disabled; it registers no keybind, schedules no work, and accesses no Unreal objects. It does NOT record equipment or gliding. Removing the mod is the recommended recovery; installing this stub is not required.
