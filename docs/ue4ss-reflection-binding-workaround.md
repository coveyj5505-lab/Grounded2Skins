# Confirmed wrapper identity and source-backed initialization-order workaround

The one-shot user log completed. Pawn: `AActor`. Descriptors: `ObjectProperty`. Both value access forms for BOTH movement/equipment: **`RemoteObjectBase`**, with `type`/`IsValid` but no `GetFullName`, `GetClass`, `IsA` or `get`. This is neither an expected UObject wrapper nor a Param that should be blindly unwrapped. See object-access-runtime-results.json.

Exact Beta `ca6f9b4c` [LuaUObject.hpp](https://github.com/UE4SS-RE/RE-UE4SS/blob/ca6f9b4c/UE4SS/include/LuaType/LuaUObject.hpp):

1. ObjectBase's `construct` (around134) creates a metatable only if one doesn't exist; final base setup (around208) sets `type()` to `RemoteObjectBase` and supplies basic validity/address methods.
2. UObjectBase aliases `Super=RemoteObjectBase` and `SelfType=Super` (around429).
3. Its `Reflection()` creates `ReflectedObject` with `SelfType::construct(...)` (around581), choosing the base pointer constructor under the `UObject` metatable name. If this is the first creation of that metatable in the mod Lua state, it installs bare-base methods.
4. The full UObject pointer constructor (around451) likewise initializes bindings only when that metatable doesn't already exist. A later component value therefore reuses the incomplete table and reports `RemoteObjectBase` with exactly the missing members seen in the user log.
5. The separately constructed [AActor bindings](https://github.com/UE4SS-RE/RE-UE4SS/blob/ca6f9b4c/UE4SS/src/LuaType/LuaAActor.cpp) keep their own metatable and full methods. This explains why V2 pc.Pawn/GetClass worked and did not prove component bindings. Both index spellings share the property pusher, so both retain the poisoned metatable.

This is a source-backed initialization-order defect consistent with direct runtime evidence. We did not execute or rebuild the native UE4SS DLL in Linux, so actual workaround success remains a Windows test boundary.

## v2.0 implementation

No Reflection calls at all. Resolve only required native UClass definitions, inspect exact field descriptors with the known V2 ForEachProperty class-metadata path, then read fields through normal indexing. Fields are explicitly owned/allowlisted: two component refs, hand occupancy, attacking/charging. UFunction signatures remain checked against actual reflected params; slot values come from the running enum. Fresh game/mod state required; no metatable patch, pointer recast, :get guess, SDK offsets or UE4SS upgrade.

Every returned component must report UObject/AActor before any member invocation. If the wrapper is still RemoteObjectBase, reject it and emit useful status rather than call nil members. Glide, equipment and attack exceptions disable only their getter/property, not the recorder. Status file says READY/PARTIAL/STOP before the user does gameplay. A partial equipment lane is enough to continue crook state validation without waiting for glide; no arbitrary block from optional wing research.

Actual Lua5.4 regression suite rejects any Reflection call, validates signatures/live slot values, simulates missing GetClass/IsA, isolates glide and equipment failures, rejects RemoteObjectBase without invoking missing members, checks timer/queue behavior. These are logic tests, not native integration proof. No previous FP fix, mesh, texture, animation, movement or inventory changes.

The new full targeted test has a5-second standing readiness gate. Continue only working lanes for equipment/normal+charged spear attacks and reusable-trinket glide/landing. Crook geometry and private cooked package remain independently validated offline, not attached yet. Native spear animation positioning remains the target, with no two-handed assumption and no changes to unarmed gameplay.
