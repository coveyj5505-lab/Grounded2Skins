ToyStoryDiscoveryV2 - staged metadata-only Windows test

This is a narrower replacement for the withdrawn crashing V1. It has NOT been tested in your Windows game. Native UE4SS calls can still crash; Lua pcall does not contain native faults. It does not read equipment/glide property values or record animations yet.

INSTALL
Close the game. Keep ToyStoryDiscovery V1 entirely outside Mods and remove only its mods.txt entry if present. Copy ToyStoryDiscoveryV2 into your existing ue4ss/Mods directory. It includes enabled.txt. If your loader requires mods.txt, add ToyStoryDiscoveryV2 : 1 without replacing existing entries. Keep working UE4SS, FreeBuild and skin packages unchanged.

FIRST TEST - STAND STILL, DO NOT JUMP
Load a copied test save. Press Ctrl+F9 ONCE and wait five seconds. This only identifies the local character. If the game stays responsive, press Ctrl+F9 once more and wait five seconds. This second press lists only property names/type descriptors on the immediate character class, not their values.
If still responsive, you may press Ctrl+F9 up to two more times, waiting five seconds between each, to list the next two parent classes. Four total presses are enough for the first returned log. Stop on any freeze, crash or Lua error. Do not spam the key. No jump, gliding, weapon switch or fight is needed for this test.

Copy ue4ss/UE4SS.log BEFORE relaunching (startup can replace it). Return it with how many Ctrl+F9 presses you made and whether the game stayed responsive.

WHY THIS IS DIFFERENT
V1 ended during the character's property scan after logging OnItemEquipped. V2 does not read arbitrary property values, stringify delegate/array/struct wrappers, scan function lists, inspect mesh/animation objects, or call any discovered gameplay functions. Each press does one bounded stage; native operations have BEFORE/AFTER markers and line endings. UObject references are reacquired each time rather than retained across keypresses. Later stages need the actual property metadata before whitelisted scalar glide/equipment reads can be designed. This is NOT a wing/crook behavior mod.

REMOVE
Close game, move ToyStoryDiscoveryV2 outside Mods, and remove only its mods.txt entry if added. No saved-game or skin changes are made by this script.
