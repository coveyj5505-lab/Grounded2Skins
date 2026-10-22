RIVET — TOY STORY SUITE — RELEASE CANDIDATE 1
Grounded 2 WinGDK, UE 5.7.4 / game release 0.6.0.3

Prepared consolidated package, NOT yet a final Windows-tested release.
Latest automatic crook and renamed combined installation await confirmation.
The previously accepted releases remain preserved for rollback.

INCLUDED
Rivet-BoPeep: accepted skin/cape, native crook, automatic carry candidate V2.6,
  hook-down roll; native spear grip/jabs/range, base damage 8, no charge/throw.
Rivet-Buzz: accepted skin and wings. F1 cosmetic toggle; gliding forces wings
  extended and landing restores preference. Flight-pose V5 included DISABLED
  because intermittent pose/tuft behavior is unresolved.
Rivet-Jessie: accepted final skin.
Rivet-Woody: accepted final skin.
Rivet-Teleport: user-accepted final V6, normal map / native hold Space travel.
Rivet-FreeBuild: accepted building autocomplete, host-authoritative.
Rivet-InvisibleArmor: accepted visual-only armor hiding, armor stats retained.
UE4SS: 3.0.1-1181-g83330635 compatible update; loader DLLs byte-identical to
  the update already tested. Official settings and LICENSE are included.

INSTALL — GAME FULLY CLOSED
1. Back up your existing ue4ss folder and dwmapi.dll OUTSIDE the game directory.
   This package supplies a self-contained Rivet mod list. If you keep other
   mods, merge their known-working settings separately; do not keep duplicate
   old copies of this suite enabled alongside Rivet-named copies.
2. Move this suite's previous Pak TRIOS (.pak/.utoc/.ucas) OUTSIDE all game Paks
   folders, including ~mods. See LEGACY-REPLACEMENTS-TO-REMOVE.txt. Renaming old
   files or moving them to another subfolder of Paks does not disable them.
   Keep original game containers (Augusta-WinGDK/global/etc.) untouched.
   Keep the old incompatible Teleport, Invisible Armor and FreeBuild Paks out.
3. Copy the included Augusta folder into the game root that already contains
   Augusta. Resulting paths must include:
   Augusta/Binaries/WinGDK/dwmapi.dll
   Augusta/Binaries/WinGDK/ue4ss/UE4SS.dll
   Augusta/Binaries/WinGDK/ue4ss/Mods/Rivet-BoPeep/Scripts/main.lua
   Augusta/Content/Paks/~mods/Rivet-BoPeep_99_P.utoc
   Do not accidentally create Augusta/Augusta.
4. Use the included mods.txt/mods.json. Enabled:
   Rivet-BoPeep, Rivet-Buzz-Wings, Rivet-FreeBuild,
   Rivet-InvisibleArmor, Rivet-Teleport.
   Rivet-Buzz-Flight is intentionally disabled. No collectors/probes/debug
   console/old cosmetic crook mod are bundled.
5. Install the suite on each participating Windows machine for consistent
   skins. Automatic native-crook creation currently supports host/standalone
   Willow only; remote-client automatic equipment remains pending.

QUICK CHECK
Pete = Woody; Max = Buzz; Hoops = Jessie; Willow = Bo Peep.
Bo Peep: load with BOTH real hand slots empty. Crook appears automatically;
  no F7. Equip main/offhand gear to hide it; clear both hands to restore it.
  Check ordinary jabs, first/third-person switches and hook direction.
Buzz: F1 opens/closes wings. Try a glide, land and check cosmetic preference.
Teleport: normal map, hover valid unlocked outpost, hold Space. Repeat trips
  and check that no floating departure door remains.
FreeBuild/Invisible Armor need no activation key.

PENDING ACCEPTANCE
- Automatic V2.6 crook, hook angle and persistence/save/reload behavior.
- Renamed containers/folders combined with the official loader configuration.
- Remote-client native crook and multiplayer accessory visibility.
- Buzz flight pose reliability (excluded from active defaults).
A pending feature is not represented as already final merely because it is
present in this package. Send UE4SS.log and any visible regression details.

OPTIONAL EXPERIMENTAL BUZZ FLIGHT
Only if deliberately testing it: set Rivet-Buzz-Flight : 1 in mods.txt and its
mod_enabled to true in mods.json, then set Enabled=true in
Mods/Rivet-Buzz-Flight/Scripts/flight_config.lua. Leave normal wings enabled.
This can reproduce unresolved visual issues; it is not part of the stable
active defaults.

ROLLBACK
Close game. Move the 8 Rivet Pak trios out and restore your backed-up UE4SS
folder/dwmapi plus the previously accepted matching skin/accessory trios.
Do not combine old and renamed replacements. Preserve save backups while
validating the automatic equipment candidate.

NAMING AND PROVENANCE
Rivet names identify this compatibility/integration package. Internal Unreal
asset paths stay original because replacement targets and references require
those names. Repacking changed container identity, not the game asset chunks.
UE4SS remains the upstream project, under its included LICENSE. FreeBuild,
Invisible Armor and Teleport started from user-supplied mods/native behavior;
Rivet compatibility code is not a claim to author the original game/mods.
See COMPONENT-VERSIONS.json, SHA256-MANIFEST.json and Validation receipts.
