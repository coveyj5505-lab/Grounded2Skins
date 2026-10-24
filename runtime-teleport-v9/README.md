# Rivet Base Teleporter V1 — multiplayer test candidate

Includes Teleport runtime V9: on-demand departures for native outposts, plus a
separate buildable base destination. This is an experimental Windows test build;
the construction and multiplayer acceptance steps below have not been run here.

## Install

Close the game. Use a COPY of a save for the first test. Host and EVERY joining
player must install the SAME Paks and Lua folder from this ZIP.

1. Back up the current Teleport Lua folder outside UE4SS Mods. Replace only the
   Teleport folder with Mods/Teleport from this ZIP; leave other Rivet mods alone.
   Keep Teleport enabled in your existing UE4SS mod settings.
2. Copy the three zRivetBaseTeleportV1_P files from Paks into the game's
   Augusta/Content/Paks directory. Keep the trio together.
3. Remove Xingxing/old cooked Teleport map/controller overrides from Paks for this
   test, keeping backups outside Paks. Run only one Teleport Lua version.
4. These assets use the current catalogs you supplied. They replace two composite
   catalogs additively and may conflict with other mods replacing those catalogs.
   Do not carry this test package across a game update without rebuilding it.

## Use

Find the new Teleporter entry under the building menu's utility/athletics category.
Its prototype recipe costs the same as a basic trail marker: two sprigs, two plant
fiber and one clover leaf. This is a test cost, not a final balance decision.

Place and finish it on clear, level ground first. It uses a pad appearance, not a
full visible outpost tube. It is a separate building ID; ordinary trail markers
are unchanged. The native marker interaction can name/customize the base marker.
The placement preview may briefly retain the native marker appearance while its
instance initializes. Scaling and extra rotation axes are disabled for this row.

Open the normal map, hover that building's marker and click Travel to Base. Native
outposts retain their normal hold-to-travel route. Base travel is selected from
the map; walking onto the pad does not randomly send you to another pad.

Use normal building demolition to remove it. The old marker/target must stop
accepting travel. Finish a new one to register a fresh destination, even if it
occupies the same spot. The arrival uses the existing native pod anchor offset;
leave a few meters clear around the pad for the first test and test indoors only
after verifying where the character arrives.

## Multiplayer and saves

The host alone creates native travel backends and revalidates every request. A
joining player sends the existing reliable controller RPC; sending it is not an
arrival confirmation. Completed buildings, target actors and doors are explicitly
replicated. Clients do not spawn local destinations. A local preview reporting
actor authority is insufficient: server network mode is also required.

The saved object is the actual native building. Backend actors and doors are
excluded from dynamic save restoration and are reconstructed for that building
after load. An idle backend has a short renewable lease, so stopping the mod does
not leave it alive forever. Demolition removes a destination immediately from
selection; an in-use backend retires until travel finishes, with a bounded expiry.
Rebuilding creates a new backend instead of reviving the destroyed one's record.

Departure actors still exist only for an actual travel request and expire after
30 seconds. None follows the player. Base destination backends remain tied to
their completed buildings, not to players. Do not mistake these intended base
destinations for the removed V7 player follower.

Before removing the Paks from a save you intend to keep, demolish all Rivet base
teleporters and save while the mod remains installed. A save containing a custom
building row still needs that row's assets. Keeping a pre-mod save copy is the
rollback for this first prototype; no save migration/repair is included.

## What passed here

63 production-Lua fixture groups: base lifecycle/replication, map/RPC integration
and existing outpost regressions. Asset checks verified all 861 native building
and 634 native recipe rows unchanged, one new row in each catalog, correct private
parent loading, four fully decoded table exports, retoc hash/round-trip checks,
and four successful legacy conversions with zero failures.

These checks cannot establish Windows placement, construction-row assignment,
demolition interaction, actual arrival position, distant-marker streaming or
real host/client save/reload. Follow TEST-INSTRUCTIONS.txt before using this on
a valued save. Do not call it a confirmed working release from local tests alone.
