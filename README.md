# Grounded 2 — Max mesh test download

[**Download Max-Mesh-Test.zip**](https://github.com/coveyj5505-lab/Grounded2Skins/raw/refs/heads/mesh-test-download/Max-Mesh-Test.zip)

A 68 MB Windows test archive containing all three `zMeshTest_P` mod files and `READ-ME-FIRST.txt`. Extract the ZIP with Windows **Extract All**.

This is a small helmet geometry change to Commander101, **not Buzz Lightyear**. Local extraction, container hashes, and Blender reopen validation passed. **It has not yet been tested in Grounded 2.**

## Install

1. Close Grounded 2.
2. Back up the original three `zCommander101_P` files outside `Augusta/Content/Paks`. Do not overwrite them.
3. Copy `zMeshTest_P.pak`, `zMeshTest_P.utoc`, and `zMeshTest_P.ucas` together into `Augusta/Content/Paks`.
4. Select Max and check the small raised area on the upper-front helmet, including the backpack variant. Test movement and animations.

## Remove

Close the game and remove only the three `zMeshTest_P` files. Restore the backed-up Commander101 trio if desired. Do not install both Max replacement mods at once.

SHA-256 of the ZIP: `0697a675afa0b3287e31d2b78c8f75bed59916f52639aa512b307158c370f148`

This test preserves the original mesh counts, skeleton, weights, section assignments, and material references. It changes 78 helmet vertices by up to 1.5 cm in both mesh variants. The packaged UCAS is uncompressed.
