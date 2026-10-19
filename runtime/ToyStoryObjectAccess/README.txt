ToyStoryObjectAccess - SHORT wrapper diagnostic, not a gameplay recorder

This replaces the failed access checks with a one-shot comparison of exactly TWO component properties. No need to attack, switch equipment, glide or test first-person.

1. Close game. Move ToyStoryAccessoryCheck and old ToyStoryDiscovery* folders outside ue4ss/Mods; remove their mods.txt entries if present. Keep working skins/UE4SS/FreeBuild untouched.
2. Copy ToyStoryObjectAccess into ue4ss/Mods. enabled.txt included; if your loader requires mods.txt append ToyStoryObjectAccess : 1 without replacing other lines.
3. Load a save, STAND STILL, press F9 ONCE. Wait5seconds. Copy UE4SS.log before restarting and send it. That's the entire test.
4. Remove this diagnostic afterward; it is not the final accessory recorder.

It logs ordinary Lua type, available member kinds, UE4SS type() tag when present, validity and full name for: V2's working pc.Pawn reference; each component's reflected property DESCRIPTOR; GetPropertyValue return; direct pawn[name] return. It does NOT call GetClass/IsA, invoke gameplay UFunctions, dereference generic :get wrappers, traverse arrays/delegates, read offsets, or change anything. Each operation is isolated with Lua pcall; missing methods won't abort the rest. Native access violations cannot be contained by Lua; this read-only diagnostic is not Windows-validated yet.

Why: exact UE4SS Beta ca6f9b4c source registers GetClass/IsA on UObject and routes GetPropertyValue and direct indexing through the same implementation. Switching those access spellings alone is NOT a demonstrated fix. Neither failed log printed the actual wrapper type, so we must identify it rather than assume absent methods imply a different supported API. Source-backed wrapper tags distinguish ObjectProperty metadata, UObject instances and Param/weak references. No full gameplay repetition is required until this is resolved.
