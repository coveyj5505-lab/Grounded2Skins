# UE4SS object-access audit after two recorder failures

## Evidence and correction

User log reports UE4SS3.0.1Beta git `ca6f9b4c`. The first recorder found `/Script/Maine.MaineCharMovementComponent:IsGliding`, checked BoolProperty ReturnValue, then failed at receiver `IsA`. v1.1 reached the same signature and failed at receiver `GetClass`. Neither called IsGliding or emitted a STATE. User action sequence was valid but not captured. Both logs contain later FreeBuild activity: these two failures were Lua recorder aborts, not the earlier V1 native crash.

It was incorrect to conclude that those methods are globally absent from this Beta. Exact Beta source registers both on UObject. The actual returned Lua wrapper has NOT been identified because neither failed recorder logged `type()`, full name, or ordinary Lua type of that value. Do not claim a specific wrapper or a proven fix before that evidence. A pending direct-index rewrite is NOT a released fix.

## Exact source trace (not latest development documentation)

Fetched both tag `v3.0.1` and log-identified commit `ca6f9b4c`:

- [Exact Beta UObject bindings](https://github.com/UE4SS-RE/RE-UE4SS/blob/ca6f9b4c/UE4SS/include/LuaType/LuaUObject.hpp): `GetClass` registered around554, `GetPropertyValue` around617, `IsA` around647. `__index` uses `prepare_to_handle(Operation::Get,...)` around502; `GetPropertyValue` uses the same routine. `prepare_to_handle` around787 resolves a property descriptor in the object's class and dispatches `handle_unreal_property_value`. Thus documented equivalence is implemented here. Merely exchanging `GetPropertyValue(name)` for `object[name]` is not a demonstrated root-cause fix.
- [Exact Beta value/function dispatch](https://github.com/UE4SS-RE/RE-UE4SS/blob/ca6f9b4c/UE4SS/src/LuaType/LuaUObject.cpp): `push_objectproperty` around397 reads the referenced UObject pointer and calls `auto_construct_object` for Operation::Get/GetNonTrivialLocal. That constructor wraps ordinary components as UObject; actors/classes/enums/functions get specialized wrappers. These normal UObject-derived wrappers are expected to expose GetClass/IsA. Operation::GetParam constructs a RemoteUnrealParam instead; this is a different path and is NOT established for our ordinary field reads.
- Same header: `Reflection():GetProperty(name)` constructs an FProperty descriptor, not a component instance. Its wrapper can be ObjectProperty and supplies `GetPropertyClass` (declared referenced class), which is not an instance to call gameplay methods on. Property metadata, class definitions and live object values must remain distinct.
- Same CPP, `call_ufunction_from_lua` around80: validates a UFunction and calling context, marshals actual parameters and returns values. Supported shape is `component:IsGliding()` (or `component['IsGliding'](component)`); a separately resolved UFunction can receive an explicit UObject context. Neither is appropriate until the receiver is a real compatible instance. Do not bypass receiver validation and invoke on metadata.
- [v3.0.1 UObject docs](https://github.com/UE4SS-RE/RE-UE4SS/blob/v3.0.1/docs/lua-api/classes/uobject.md), [requested web documentation](https://docs.ue4ss.com/lua-api/classes/uobject.html). Official raw-source/docs were accessible; docs site previously returned proxy403. Generic `:get()` is only appropriate for wrapper types that document it, such as RemoteUnrealParam/weak references. Do not blindly unwrap an unknown value.

The old V2 used `pc.Pawn` directly, then called `pawn:GetClass()` and traversed UClass superclasses for property NAMES only. It did not read the movement/equipment values, check their wrapper types, or demonstrate that they expose UObject members. V2 success proves the player identity/class path, not component-reference handling. The recorder added `Reflection:GetProperty` followed by `GetPropertyValue` on exactly2ObjectProperties. Its initial validity check succeeded but IsValid is available on other remote wrappers too, so that did not prove UObject identity.

## Shortest necessary runtime evidence

`ToyStoryObjectAccess` is a separate single-shot diagnostic. Standing in a loaded save, F9once, wait5seconds, return UE4SS.log. No spear attacks, equipment changes, gliding, camera testing or three-minute recording needed.

It logs ordinary Lua type, available-member kinds, safe optional `type()` tags, validity/full identity for V2's direct pawn; both property descriptors; each GetPropertyValue result; each direct-index result. It does NOT invoke GetClass/IsA, gameplay UFunctions, generic `:get()`, offsets or recursively traverse objects. Missing methods and each diagnostic operation are isolated. Native faults remain outside Lua pcall protection. No diagnostic can prove native safety through mock tests alone.

These fields distinguish metadata-versus-instance, Param/weak wrappers, specialized UObject wrappers or another representation; currently the two logs alone cannot. If both access forms are unexpected, the next route can use the exact known component classes and owner filtering rather than arbitrary graphs, but no additional scan has been implemented or requested now.

## Resilience implemented offline, full recorder withheld

The pending recorder source is `runtime/pending/AccessoryRecorder-main.lua.disabled`. The loadable old recorder is replaced by a no-keybind withdrawn stub; old source is retained under runtime/quarantined. It is not the next Windows test. Getter/property/enum Lua failures disable only that operation. Tests force glide failure while equipment/attack continue, and equipment failure while glide/attack continue. Native access violations cannot be isolated this way and are never claimed catchable.

`pipeline/test_accessory_check.py`:6realLua5.4 groups pass, including missing GetClass/IsA and intentionally forbidden GetPropertyValue in a DIRECT-access mock. This validates code branches, NOT that direct access will fix the actual Beta reference. `pipeline/test_object_access_probe.py`:3realLua5.4 groups pass for distinct metadata/live-object mock types, missing optional methods, one access failure while other fields complete, and no-pawn retry/single-shot behavior.

After identifying actual wrapper type, use the supported access path, then release ONE complete targeted equipment/spear/reusable-trinket check. No Grounded2 SDK offsets, first-person changes or skin replacement required. Crook data-only asset already passed Blender/CUE/IoStore validation and remains the accessory priority. Glide diagnostics must not gate equipment-only cosmetic attachment progress once actual equipment access is available. Crook remains visible in FP/TP; native spear hand positioning replaces the withdrawn two-handed constraint. Wings use glide only after observed getter transitions.
