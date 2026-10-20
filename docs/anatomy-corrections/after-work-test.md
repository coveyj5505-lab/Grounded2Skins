# After-work anatomy tests

These are separate new test builds. The v0.3 ZIP, its Lua mods, and Woody V2 remain unchanged. No installers or replacement mods.txt are included.

## Woody V3

`Woody-Pelvis-V3-Test.zip` contains one self-contained Pete replacement trio. Close the game and move the active older Woody/Pete trio outside `Augusta/Content/Paks` (typically `zWoodyFP_P` or `zWoodyPolishV2_P`). Copy the three new files from `Paks` into that folder. Leave the other characters and accessories installed. Do not keep two Pete replacements active.

Check Woody standing, running and sitting. The seated pelvis should meet the thighs, with the belt above the hip hinges. Boots and circular pull ring retain V2's corrections. First-person sections, hands, face, native skeleton and textures were preserved. The offline poses are synthetic FK checks, not extracted gameplay animations.

Rollback: remove `zWoodyAnatomyV3_P.pak/.utoc/.ucas` and restore the previous Woody trio.

## Optional Buzz flight-pose test

`Buzz-Flight-Pose-V1-Test.zip` adds an independent cosmetic mesh and UE4SS mod. Keep Buzz and v0.3's wing/crook mods installed. Copy its three `Paks` files into `Augusta/Content/Paks`. Copy `Mods/BuzzFlightVisual` into the existing UE4SS `Mods` folder and add this line to the existing `mods.txt`:

```
BuzzFlightVisual : 1
```

The packaged flight config is enabled automatically; the repository experiment config deliberately remains disabled. There is no required debug key. Start as Buzz/Max, glide in third-person using an actual successful tuft deployment (including the reusable trinket), land, and switch views. No special probe recording is needed; UE4SS.log records state changes and load/fallback milestones automatically.

Expected: standing/manual wings retain native presentation; actual third-person gliding uses the corrected forward-flight visual; landing or first-person restores native presentation. Flight arms are uniformly fitted from original source geometry at the armor's side openings. The pose is static, the original tuft visual remains, and the new visual is local-client only. Windows loading, coexistence, and server behavior are unconfirmed until tested. Engine functions are checked against live reflected signatures; no SDK offsets or actor/camera/movement transforms are used.

Rollback: remove the new `BuzzFlightVisual` entry/folder and `zBuzzFlightTest_P` trio. The v0.3 modules and character files were not overwritten.

## Offline evidence

Both packages were re-extracted and checked with CUE4Parse. Woody's two changed meshes preserve all other 19 asset chunks, native references and 50 texture mips. Buzz's four LODs, root-rigid weights, private material/atlas dependencies and decoded textures match the corrected candidate. Source and actual cooked previews were visually inspected. Controller and adapter fault-injection tests cover landing, view switches, concurrent wing updates and rollback. These checks do not replace Windows testing.

The previous arm-at-head and below-chair-pelvis previews are rejected. Their earlier serialization checks did not establish acceptable anatomy.
