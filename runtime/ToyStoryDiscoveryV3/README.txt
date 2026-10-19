ToyStoryDiscoveryV3 - F9 alone; combined metadata and scalar state snapshots

Close game. Remove ToyStoryDiscovery and ToyStoryDiscoveryV2 from Mods and remove their entries from mods.txt if present. Copy this ToyStoryDiscoveryV3 folder to ue4ss/Mods. enabled.txt is included; if your loader requires mods.txt, add ToyStoryDiscoveryV3 : 1, preserving other entries. Do not change UE4SS, FreeBuild or skin packages.

ONE SESSION TEST - USE F9 ALONE (NO CTRL)
Use a copied save. Equip a dandelion tuft and choose a safe drop with enough air time.
1. Standing, unarmed: press F9 once. Wait 5 seconds. This first press lists up to 8 classes and discovers relevant typed scalar fields, then reads them. If game freezes/crashes, stop and preserve UE4SS.log before restarting.
2. If responsive, jump/drop and deploy the tuft. Once visibly GLIDING press F9 once.
3. After LANDING press F9 once.
4. Equip a SPEAR, standing idle: F9 once.
5. Hold a SHIELD (note other equipment): F9 once.
6. Return UNARMED with NO SHIELD: F9 once.
Optional: F9 while sitting, sprinting, or mid-spear attack. Note any skipped steps or different order. If safe/practical, an ordinary airborne jump without deploying the tuft is useful as an extra comparison; identify its snapshot order in your notes.

Send ue4ss/UE4SS.log with your snapshot order. Copy it BEFORE relaunching. A snapshot is not continuous recording, so press during the desired state. Do not spam F9; wait between snapshots. First standing snapshot performs discovery; later ones reuse only field name/type strings and reacquire the pawn. Standing/gliding/landed comparison is intended to test which candidate fields change, not assume any named property proves gliding.

BOUNDARIES
This is a new Windows-UNTESTED probe: native calls can still crash and Lua pcall cannot catch native faults. V2's successful metadata stages do not validate these new scalar reads. V3 only reads Bool/Byte/Int/Int64/Float/Double fields found in actual metadata and matching movement/glide/equipment/camera keywords (max96). It never reads arrays, delegates, structs, arbitrary object values or guessed property names. Runtime returns other than booleans/numbers are not converted or traversed. It does not activate gliding, attach props, equip items, play animations, change damage/movement, or hide the tuft. Equipment object references are metadata only; a separate read may be necessary if equipment state has no useful scalar fields. Fields may not expose actual glide state; further testing is possible. Logs before/after native calls localize failures but do not guarantee durable log flush on a native crash.

Remove by closing game and moving this folder outside Mods; remove only its mods.txt entry if added.
