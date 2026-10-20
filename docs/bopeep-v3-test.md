# Bo Peep V3 model and crook test

Offline validated; Windows pending. Incremental source-informed correction preserves the native 192-bone rest skeleton, first-person head/body material split, retained skin weights, UVs, materials and all other skins. Excessive torso/neck fitting stretch is reduced; the head shape is translated without rescaling. Upper hips are narrowed and cape length/width reduced. A disconnected 56-vertex source helper plate incorrectly weighted to the ankles is omitted from the playable mesh and preserved separately in Blender. Original body, crook and source remain preserved.

Fresh native read-back validates both cooked meshes, all four LODs, exact intended positions/indices/UVs/weights and preserved skeleton. Only the two body mesh chunks changed; fourteen other chunks remain byte-identical. Controlled Blender pose previews are not gameplay validation. Cape remains bone-weighted, without cloth simulation.

Game closed: back up and remove only the previous Bo Peep skin trio (usually zBoPeepFP_P) from Augusta/Content/Paks. Copy the three zBoPeepV3_P files there. KEEP zBoCrookAsset_P and all other character skins. Replace BoPeepCrook/Scripts/main.lua with the ZIP copy. Keep BoPeepCrook : 1 in mods.txt. This is the same v0.2 grip/first-person script already delivered separately; its Windows result remains pending. F9 toggles the cosmetic. No spear animation substitution or combat changes.

Inspect standing, walking, sitting, cape, first-person crook and equipment hiding. Restore the backed-up skin trio and previous Lua script to roll back. Do not install two Bo Peep body skins simultaneously.
