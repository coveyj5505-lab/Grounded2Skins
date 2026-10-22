# Teleport V2 — Lua multiplayer test candidate

This replaces the failed old Teleport cooked override. **Windows startup, travel and multiplayer are not yet confirmed.** It uses the current native outpost teleporter/door functions and the existing reliable server travel request; it ships no Paks or replacement player controller/map Blueprints.

## Install on BOTH host and client

1. Close the game. Keep the old `Xingxing_OutpostMapTeleport_905_P` trio and failed `zTeleportUE57_99_P` trio removed from Paks. Each trio means `.pak`, `.utoc`, `.ucas`. Do not reinstall either.
2. Copy the `Teleport` folder into the existing UE4SS `Mods` folder on each machine.
3. Add `Teleport : 1` to each existing `mods.txt`, preserving the working FreeBuild, InvisibleArmor, skins and accessories.
4. Start the host and load a world. Allow about five seconds for `[Teleport UE57 V2] SERVER_RPC_HOOK_READY` in the host's UE4SS log before testing a connected client.

The matching Lua mod must run on the host **and** on each client using the F8 shortcut. A client-only install cannot supply the server handler. No loader update or additional Pak is included.

## Test

- Host: open the map, hover an **unlocked outpost marker**, and press **F8**. The mod asks the game's native outpost travel system to move that player. It is not a free-coordinate or waypoint teleporter.
- Connected player: with the same files installed, do the same. Confirm that the connected player moves and the host remains where they were.
- Also verify ordinary outpost travel, map close/reopen, leaving/rejoining, and exit to desktop.
- Retain the host log and client log. `CLIENT_SENT` means a request was sent, **not** arrival confirmed. `REQUESTED` similarly requires checking arrival. `SERVER_GUARDED_STOP`/`GUARDED STOP` identifies a rejected schema, unavailable destination or failed setup; send the log.

F8 is separate from Buzz's F1 wing toggle. The ordinary map buttons are not replaced. If F8 conflicts with another mod, the single `RegisterKeyBind(Key.F8,...)` line can be changed on the relevant client; the native request protocol does not depend on the key.

## Behavior and current limits

The server validates authority, registered destination and native outpost lock state. It creates a hidden temporary native departure at the requesting player's transform, supplies that player's interaction instigator, and invokes native outpost travel. Temporary actors have a30-second lifespan and are destroyed if setup fails. It does not unlock outposts, force world coordinates, change character meshes or install old Blueprints.

For connected players, the current stock server event has no departure to use for a remote map request. The Lua posthook completes that request on the host. The stock event may emit an `Accessed None` Blueprint warning for its missing departure before the posthook runs; this path needs actual Windows confirmation. Regular native requests with an existing departure, and cancelled requests, are left alone. Script posthook semantics were checked against installed UE4SS83330635 source. Registration runs from LoopAsync; world reads and travel actions are queued to the game thread.

Sixteen actual-Lua fixture groups pass, including correct requesting pawn, independent per-controller cooldowns, client requests without local movement, server authority, normal travel preservation, map visibility, locked/stale destination rejection, setup cleanup, no actor creation at startup, and hook registration outside the game thread. Fixtures do not prove native RPC delivery or successful travel in Unreal.

Rollback: close the game, remove the `Teleport` Lua folder/entry and restart. Keep the failing Teleport Paks removed. Working character, FreeBuild and InvisibleArmor files are unchanged.
