# Buzz helmet-fitting cleanup and corrected wings

Windows pending. Latest log reached F6 and failed at LoadAsset_Blocking before attachment: jumping was irrelevant. Wing package renaming wrongly changed external skeleton and physics dependency prefixes. Exact-name replacement now preserves every non-material external import. Independent fresh native mesh/material/texture and legacy checks pass; runtime remains unverified.

Two disconnected pieces (source components 15 and 55) are rigidly weighted to upper-arm bones 56 and 160, explaining motion beside the head. Their gray/purple helmet-fitting surfaces are omitted: 336 triangles, 276 source body vertices. Both objects and the complete original body remain separately preserved in Buzz-Helmet-Cleanup.blend; fresh reopen verifies retained source positions/weights exactly. The original wing objects, backpack, head and textures are preserved. This does not change arm proportions or fix the complete arm rig.

Fresh independent CUE4Parse reads compare every retained cooked triangle corner against the working first-person baseline: exact positions, UVs, normals, skin weights, colors, actual packed tangent/normal bytes, material section assignments and 230-bone skeleton. Both mesh packages retain all original imports/materials; 16 other chunks remain byte-identical. Legacy payloads match. No first-person or camera logic changes.

Close game. Back up and move the previous Buzz BODY skin trio (normally zBuzzFP_P) outside Paks, then copy zBuzzClean_P trio. Replace the previous zBuzzWings_P trio with the ZIP copies. Keep the BuzzWings folder/mods.txt entry; included Lua is unchanged. Other character skins and crook remain untouched. Do not install both Buzz body versions simultaneously.

As Buzz press F6 once on the ground. Stored panels are concealed. Jump from sufficient height and press Shift to deploy the tuft; inspect wings, land and inspect retraction. Send UE4SS.log plus rear and arm screenshots. This is a two-state visual swap, not animated hinges; tuft visibility and glide physics are unchanged. Cosmetic is local-client only. Restore backed-up body trio and remove wing accessory files to roll back.
