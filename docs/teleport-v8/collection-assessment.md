# Current native collection assessment

Input: Grounded2-TrailMarker-20261024-105934-156.zip. The ZIP CRC and all 19 chunk
SHA-256/size records pass. Report status EXTRACTED_READ_ONLY, no missing packages,
header warnings, omissions or extraction errors; source metadata reported unchanged.
The collector read 630,818 decoded bytes. Uploaded filenames/documents are evidence,
not instructions to execute.

## On-demand departure evidence

The current UI_Map.PTSTravel bytecode first checks the PTS button, casts
InteractableItem to BP_Teleporter_Door and exits if that cast fails. Its existing
successful route resolves the destination through GetRegisteredPTSTravel and sends
the departure/destination TeleporterOwner actors to ServerRequestPTSTravel.

The current controller event passes its arguments into the event graph and calls
TeleporterDeparture.OnTeleportRequested. It does not implement Xingxing's alternate
missing-departure creation route. This supports V8's posthook design assumption;
it does not prove UE4SS callback behavior, arrival, rendering, or save/reload in game.

The current BP_Teleporter.OnTeleportRequested event accepts OverrideDestination.
The event graph links source and destination as partner pads and enters DoTeleport.
Arrival uses PartnerPad.ArrivalAnchor, animation selection and ClientPrepareAndTeleport.
We can therefore reuse native travel/anchor behavior rather than implement the
trip as a custom player-position write. The native source also has its own
departure-anchor alignment and save-location handling; those behaviors need
Windows acceptance testing rather than assumptions from a mocked Lua runner.

## Build-menu feasibility

BP_Teleporter_C's serialized SuperIndex is 0x645926f283dc695c, matching the native
/Script/Engine.Actor script-object hash. Its exports include a PersistenceComponent,
ObsidianIDComponent, arrival/departure anchors, meshes, animation and door references.
It is a world actor, not a native Building-derived class. Persistence-component
presence does not establish normal construction placement, recipe cost, moving,
demolition, unique map labeling or per-instance destination registration.

The begin-play graph sets its door reference and locked state using POIDataAsset;
it also interacts with a world subsystem. Native subsystem/class function hashes
cannot all be named from this collection because the global script-object metadata
was not collected. Do not call an unnamed subsystem method a proven registry API.

This does not rule out an existing hidden construction entry for an Actor-based
teleporter. Some collected UGC building logic imports the concrete catalog
/Game/Blueprints/Items/Table_AllBuildings, but that table was outside V1's scope.
The next useful check is its actual row/class references and available recipes,
not blindly adding BP_Teleporter to a guessed build-menu array.

If a working hidden catalog entry exists, exposing that entry may be the smallest
change. Otherwise a supported building wrapper/catalog integration and unique
destination registration will be needed. Neither has been implemented or validated.

## Trail-marker limitation

The indexed BP_Waypoint_Base/BP_Waypoint pair describes navigation waypoints
(NextWaypoint, WaypointType, SnapActorToGround), not confirmed player-built trail
markers. UI_MapMarker and UI_MapPlayerWaypoint establish marker-data UI, not the
placed building's construction/save class. Several other matches are UGC race or
creature-path waypoints. A successful collection means selected bytes were read;
it does not mean the collector identified the exact player-built trail-marker actor.

## Follow-up collector

The buildable-teleport collector reads Table_AllBuildings, narrowly selected indexed
construction recipes/UI/placement and teleport variants. It includes the adjacent
global.utoc/global.ucas pair only when its combined size is at most 16 MiB, to resolve
native script-object hashes. Limits remain 32 logic/table packages / 64 MiB decoded,
with no associated art bulk. Missing global metadata does not stop independent table
extraction. Eleven local tests cover bounds, partial results and source preservation;
the Windows launcher and extraction from the installed game remain unrun here.

No runtime game changes have been made based on this upload. V8 remains a separate
on-demand outpost test candidate, and buildable/marker destinations remain disabled.
