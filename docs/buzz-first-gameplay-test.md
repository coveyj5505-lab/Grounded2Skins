# Buzz first gameplay test

The targeted stock compatibility assessment is complete enough for the user-authorized first gameplay test. All 52 weighted bones are valid and present by name in stock Max. Stock and recovered references are not identical; controlled +/-45 degree pinky local-axis tests show sensitivity up to 1.085 cm between frame choices, not a demonstrated game defect. No unsupported bind correction was made. Stock has 15 body setups/14 constraints; the preserved custom reference has 18/17. Full collision shape/retarget-policy decoding is deferred. Original rig, wing archives, eight textures, source meshes and previous working mods are untouched.

The **private**, independently read-back first test ZIP is at `/workspace/mod-work/buzz-delivery-stage/Buzz-Lightyear-First-Gameplay-Test.zip`. Its manifest is [buzz-atlas-release-manifest.json](buzz-atlas-release-manifest.json). It contains the zBuzzAtlasTest_P trio, exact Windows instructions, checksums, offline reports and front/back previews. No Buzz runtime compatibility is claimed. Do not publish the supplied model/texture/mod payloads; retain the existing source-license limitation.

Final material strategy: clone the original stock MI and four encoded atlas textures to `/Game/_BuzzMod/Art/Characters/Player_Male01/Textures/`. Original mesh slot0 imports this private MI. Its four guarded unversioned TextureParameterValue records resolve Albedo/Normal/RMA/SSSMask to the matching private C/N/RMA/SSS assets, with import hashes matching actual private public exports. MM_Character remains the original game parent. All native/property bytes, including the MI cached shader payload, are preserved. No original material or texture path is overridden. Unused Commander head texture packages are excluded; Max body/backpack, empty hair variants and their custom physics dependencies are retained.

A legacy-to-Zen cloning attempt was rejected: independent readback found UnknownPackage substitutions for missing external original-game package context. Those private experimental artifacts are **not** shipped. The final writer patches the original Zen name batches and CityHash64 name/package/public-export references directly, rebuilds package store entries and preserves unrelated external imports. Repackaging uses the proven retoc pack-raw pipeline with a new matching container identity. Its expected counts now derive from the supplied manifest, rather than assuming the original17packages/26chunks.

Final verification: 14 packages,19chunks, retoc verify passed and all raw chunks round-tripped byte-exact. Both meshes independently parsed by unmodified CUE4Parse native LOD readers:19,609 vertices/20,124 triangles, one atlas section, original230bones/rest transforms, exact encoded positions/indices/global joints/weights/colors, half UVs and valid packed normals. Every original external mesh package import is retained except the deliberate private MI substitution. CUE4Parse read all50mips and their encoded hashes match the writer. Independent BC3 decoding gives mean absolute RGB error1.195/255 against the atlas. UV affine reconstruction verifies original repeat bounds and vertical orientation. CPU Blender emission previews made from actual final decoded streams were reviewed; they verify recognizable face/eyes/chest/backpack and omitted extended wings, not Unreal shading. See [buzz-atlas-final-validation.json](buzz-atlas-final-validation.json).

Installation: close the game; move Commander101, zMeshTest and any earlier Buzz Max-replacement trios **outside the entire Paks tree**, retaining backups. Copy only zBuzzAtlasTest_P.pak/.utoc/.ucas directly to `Augusta/Content/Paks`. Do not touch Augusta-WinGDK.* or global.*. Select Max. Removal: close the game and move the Buzz trio out, then optionally restore Commander101. Simplified opaque shared shading, flat normals, matte RMA, no new facial animation and distant atlas bleeding are known limitations. All runtime behavior, texture streaming, equipment/hands and animation interactions need the user's Windows test.

## Reproduce the final isolation and packing

Existing validated stages are retained; do not repeat model extraction or rigging.

```sh
export PYTHONPATH=/workspace/toolchains/material-python
python pipeline/isolate_buzz_material_zen.py \
 /workspace/mod-work/buzz-test-stage/textured/raw \
 /workspace/mod-work/stock-max-stage/chunks/0cfec9856be41dcc00000001 NEW_PRIVATE_RAW
python pipeline/repackage_iostore.py NEW_PRIVATE_RAW \
 /workspace/mod-work/input/commander/zCommander101_P.pak NEW_PACKAGE \
 --mod-name zBuzzAtlasTest_P
```

The actual validated package work is `/workspace/mod-work/buzz-test-stage/final-zen-package` and authoritative readback stage is `/workspace/mod-work/buzz-delivery-stage` (earlier final-package/conversion directories were rejected and are not the release).

For the retained final readbacks, rerun validation to a new file:

```sh
PYTHONPATH=/workspace/toolchains/material-python python pipeline/validate_buzz_atlas_final.py \
 /workspace/mod-work/buzz-delivery-stage \
 /workspace/mod-work/global-stage/reports/reference-skeletons.json NEW_REPORT.json
blender -b -t 4 --python-exit-code 1 --python pipeline/render_cooked_buzz_preview.py \
 -- /workspace/mod-work/buzz-delivery-stage
```

The validator was rerun successfully, with stronger checks on complete external imports and section mappings. It uses existing independent CUE4Parse reports/mip binaries, not fabricated outputs. Retained command logs and metadata reside in the private stages. Blender CPU Cycles must disable denoising in this build; headless EEVEE failed EGL initialization and was not used for the reviewed previews.
