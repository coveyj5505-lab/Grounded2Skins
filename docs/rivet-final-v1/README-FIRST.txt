RIVET TOY STORY — FINAL v1.0
Grounded 2 WinGDK — UE 5.7.4 / game release 0.6.0.3

All included component versions were accepted by the user. This consolidated,
renamed installation was validated offline; it has not itself run in Windows.

INSTALL — CLOSE THE GAME FIRST
1. Back up your current ue4ss folder, dwmapi.dll and existing mod Pak trios
   OUTSIDE the game folder. Preserve the working installation for rollback.
2. Move the old suite's Lua folders OUTSIDE ue4ss/Mods:
   BoPeepCrook, BoPeepNativeSpear, BuzzWings, BuzzFlightVisual,
   FreeBuild, InvisibleArmor, Teleport, and any obsolete collectors/probes.
   Old enabled.txt files can load duplicates even if mods.txt was edited.
3. Move the old skin/accessory Pak trios OUTSIDE ALL game Paks folders.
   See LEGACY-REPLACEMENTS-TO-REMOVE.txt for previous filenames. Include old
   incompatible Teleport/Invisible Armor/FreeBuild Paks. Keep ORIGINAL game
   files such as Augusta-WinGDK and global containers untouched.
4. Copy this ZIP's Augusta folder into the game root that already contains
   Augusta, merging the folders and replacing the matching suite files.
   Check these paths (no duplicate Augusta/Augusta nesting):
   Augusta/Binaries/WinGDK/dwmapi.dll
   Augusta/Binaries/WinGDK/ue4ss/UE4SS.dll
   Augusta/Binaries/WinGDK/ue4ss/Mods/Rivet-BoPeep/Scripts/main.lua
   Augusta/Content/Paks/~mods/Rivet-BoPeep_99_P.utoc
5. Use the included mods.txt AND mods.json. All six Rivet Lua mods are enabled.
   No installers, collectors, developer console, or F7 activation are required.
   If you maintain unrelated mods, preserve their backups and merge their
   compatible entries separately instead of retaining duplicate suite copies.

CONTENTS / CONTROLS
Pete = Rivet-Woody. Hoops = Rivet-Jessie.
Max = Rivet-Buzz. Willow = Rivet-BoPeep.

Rivet-BoPeep: accepted skin/cape and native crook V2.8. Original accepted hook
  orientation (cosmetic rotation was dropped). Automatic carry when BOTH
  actual hands are empty; equip real main/offhand gear to hide, clear both
  hands to restore. Native spear grip/jabs/reach; base damage 8, no charge or
  throw. No F7. Current automatic item creation supports host/standalone Willow;
  remote-client automatic equipment remains a separate unfinished feature.
Rivet-Buzz-Wings: F1 toggles cosmetic wings. Actual gliding always opens them;
  landing restores the selected cosmetic preference.
Rivet-Buzz-Flight: ENABLED. User accepted forward flight with a brief tuft flash
  at glide start before it disappears; no further polishing included here.
Rivet-Woody / Rivet-Jessie: accepted final skins, no new geometry changes.
Rivet-InvisibleArmor: automatic visual armor hiding; armor stats preserved.
Rivet-FreeBuild: automatic building completion on host; crafting unchanged.
Rivet-Teleport: final V6. Normal map, hover valid unlocked outpost, hold Space.
  Native progress circle/animation/travel retained; no F8 teleport command.

The compatible UE4SS 3.0.1-1181-g83330635 update is included. Loader DLLs are
byte-identical to the tested update; official settings and LICENSE included.
Rivet names identify the mod folders/Pak containers. Engine-internal asset
paths remain unchanged so replacements and references resolve correctly.

MULTIPLAYER / VALIDATION
Install on each participating Windows machine for matching skins and local
visual mods. FreeBuild needs host authority. Remote-client automatic crook and
accessory visibility across all network situations have not been finalized;
this final package preserves the accepted current behavior rather than claiming
new multiplayer support. Do not remove its private item assets from a save that
contains the crook without first restoring/removing that item appropriately.

All 8 renamed containers were verified with retoc and extraction; game asset
chunks match their accepted source packages byte-for-byte. Lua syntax, enable
lists, runtime installation receipts, and packaged crook/Teleport fixture checks
passed. See Validation and SHA256-MANIFEST.json. A renamed combined-installation
issue can still require a Windows repair; component acceptance is not a claim
that this new combined installation was already Windows tested.

ROLLBACK
Game closed: move the 8 Rivet Pak trios out and restore the previous matching
Pak trios and backed-up UE4SS folder/dwmapi. Never load old and renamed suite
replacements together. Keep saves backed up when changing installed mods.

PROVENANCE
Rivet compatibility/integration package. UE4SS is an upstream project under
its included LICENSE. FreeBuild, Invisible Armor and Teleport began with
user-supplied mods/native behavior; this naming does not claim authorship of
the original game, character assets, or third-party mods.
