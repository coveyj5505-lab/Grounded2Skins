# Resized native LOD and Zen package: offline-validated


**Source clarification:** the 230-bone input is recovered from the third-party Commander101 mod. Stock-Max hierarchy/rest-pose equality has not yet been verified; the final test ZIP is paused for the [compatibility assessment](commander-stock-max-assessment.md).
The final source rig is at:
`/workspace/mod-work/rig-stage/skinned-stowed-v9/Buzz-Grounded2-skinned.blend`.
It contains eight packed textures, the visible skinned Buzz and both preserved
wing collections. Independent fresh reopening and ten controlled poses passed.
See `buzz-rig-validation.json` and `buzz-visual-review.json` for exact scope.

The cooked geometry has **19,609 render vertices, 20,124 triangles, seven
sections, 230 required bones and 63 active bones including weighted-bone ancestors**.
Source material slot 0 was only the removed marker, hence seven used sections
from eight Blender material slots. UNORM8 quantization retains at most four
nonzero influences from the original Blender rig's maximum of five, with exact
integer total 255. There is no top-eight pruning of meaningful weights.

The writer supports the two hash-guarded Commander101 layouts, not arbitrary UE5.6
projects. It writes section flags/ranges/palettes/influence limits, required and
active bone arrays, streamed byte count, five variable-size buffers and bounds.
It preserves the original materials/reference-skeleton bytes and empty native
resource tails. The existing Zen header size/imports/package identity remain;
the skeletal export size and zero-length bulk map's affected serial offset are
relocated. The latter points four bytes past the new LOD end relative to the
Zen payload, even though its bulk size is zero.

| Asset | New LOD range | Old chunk bytes | New chunk bytes |
|---|---|---:|---:|
| Body | 32898..1138608 | 15761284 | 1138708 |
| Backpack variant | 32922..1138632 | 15761308 | 1138732 |

`resized-package-validation.json` records exact output hashes and validation.
Both full LODs were decoded by unchanged CUE4Parse `GAME_Grounded2` constructors
**after** retoc repacking/unpacking. Positions, triangles, section assignments,
colors, global joint IDs and integer weights match exactly; UVs match their
intended float16 conversion and packed normals match expected precision. Required
bones, active ancestry, original rest transforms and bounds pass readback. Retoc
independently reads relocated Zen export sizes/bulk offsets. All 26 container
chunks round-trip, all 17 asset packages convert to legacy with **zero failures**,
and 23 non-header/non-mesh chunks are unchanged. No usmap was needed for this work.

## Reproduce after the rig/export/standalone encoder

Use the steps in `buzz-rigging.md` first; all output directories below must be new.
Replace `stage` with the new stage directory containing `native-buffers`.

```bash
python pipeline/write_resized_lod.py /workspace/mod-work/retoc-raw "$stage/native-buffers" /workspace/mod-work/global-stage/reports/reference-skeletons.json "$stage/cooked"
python pipeline/extract_reference_skeleton.py /workspace/mod-work/reports/commander-packages.json "$stage/cooked/raw/chunks" "$stage/cooked/reference-skeletons.json"
python pipeline/repackage_iostore.py "$stage/cooked/raw" /workspace/mod-work/input/commander/zCommander101_P.pak "$stage/package" --mod-name zBuzzGeometry_Experimental_P
export DOTNET_ROOT=/workspace/toolchains/dotnet
export DOTNET_CLI_HOME=/workspace/toolchains/dotnet-home
export NUGET_PACKAGES=/workspace/toolchains/nuget
/workspace/toolchains/dotnet/dotnet build pipeline/native-lod-probe/NativeLodProbe.csproj -c Release -p:CUE4PARSE_SKIP_NATIVE=true -m:2
/workspace/toolchains/dotnet/dotnet pipeline/native-lod-probe/bin/Release/net10.0/NativeLodProbe.dll "$stage/package/unpacked/chunks/cd809abc483f179000000001" "$stage/cooked/reference-skeletons.json" /workspace/mod-work/reports/commander-packages.json "$stage/readback-0"
/workspace/toolchains/dotnet/dotnet pipeline/native-lod-probe/bin/Release/net10.0/NativeLodProbe.dll "$stage/package/unpacked/chunks/8021448bfc8c514500000001" "$stage/cooked/reference-skeletons.json" /workspace/mod-work/reports/commander-packages.json "$stage/readback-1"
mkdir "$stage/zen"
/workspace/mod-work/bin/retoc dump-test "$stage/package/mod/zBuzzGeometry_Experimental_P.utoc" "$stage/zen" 10382837047560405197
/workspace/mod-work/bin/retoc dump-test "$stage/package/mod/zBuzzGeometry_Experimental_P.utoc" "$stage/zen" 4994928478026736000
python pipeline/validate_resized_package.py "$stage/native-buffers" "$stage/cooked" "$stage/package" "$stage/readback" "$stage/zen" /workspace/mod-work/retoc-raw /workspace/mod-work/global-stage/reports/reference-skeletons.json "$stage/resized-validation.json"
```

Retoc `to-legacy` additionally needs a separate new input folder containing a copy
of the generated trio plus the already supplied `global.utoc/global.ucas`:

```bash
/workspace/mod-work/bin/retoc to-legacy "$stage/legacy-input" "$stage/legacy" --no-shaders --no-script-objects --no-parallel --verbose
```

Inspect its summary: exit status alone is insufficient; this run reported
`Extracted 17 (0 failed) legacy assets`.

## Exact remaining work

The eight packed Buzz textures are valid **Blender** materials, not cooked Unreal
material assets. The experimental package intentionally retains nine original
Commander/Max material references. Source Buzz section IDs therefore do not yet
select compatible Buzz shaders/textures. Its colors, opacity, eye/skin shading and
normal/roughness maps are not ready for a finished playable release.

Next implement/test a compatible material/texture route: inspect existing game
material parameters/parents, then either build compatible cooked instances or
bake/rebind a texture atlas to a proven existing parent and rewrite its matching
texture mip payloads. Native texture metadata already shows DXT5 base colors, BC5
normals, DXT1 RMA/SSS, with high-resolution mips in bulk chunks. These require their
own writer and independent texture readback; mesh success does not establish that.

The six game material instances are external to the uploaded reference mod:

```
/Game/_Augusta/Art/Characters/Player_Male01/Textures/MI_Character_Male01_Max_Apparel01
/Game/_Augusta/Art/Characters/Player_Male01/Textures/MI_Character_Male01_Max_Apparel02
/Game/_Augusta/Art/Characters/Player_Male01/Textures/MI_Character_Male01_Max_ArmsLegs
/Game/_Augusta/Art/Characters/Player_Male01/Textures/MI_Character_Male01_Max_Head
/Game/_Augusta/Art/Characters/Player_Male01/Textures/MI_Eye_Human_Max
/Game/_Augusta/Art/Characters/Player_Male01/Textures/MI_Human_Hair_Afro_Max01
```

Their actual parameter tables/parent shaders are not available in the current
uploads. The retained Windows helper at
[pipeline/local-game-extractor/Extract-Selected.ps1](../pipeline/local-game-extractor/Extract-Selected.ps1) already
selects these and four other relevant dependencies from the original matching
`Augusta-WinGDK.utoc/.ucas`, without unpacking the full archive. This inspection
would resolve the material-parent uncertainty; it is not a mesh/skeleton blocker.
Do not repeat extraction or request globals/usmap for completed mesh work.

Only Windows Grounded2 can validate actual animations, equipment, hands, seating,
render bounds, post-process deformation and in-game clipping. The prior
Commander101 fixed-size edit is user-tested; the new resized Buzz geometry is
**not**. Physics, collision, movement, inputs and gliding assets remain unchanged.
Facial-expression animation and wing deployment remain unimplemented.

## Optional geometry-only Windows test

The generated trio is local at `rig-stage/package-v9/mod`. It is an experimental
geometry test with original material references, **not the finished textured Buzz
mod**. Keep the reference originals in a backup directory outside Paks; do not
overwrite them. Other Max replacement mods can override this package and must be
moved outside Paks for an unambiguous test. Copy only this distinct trio into
`Augusta/Content/Paks` if conducting that geometry test. Removal means removing
only `zBuzzGeometry_Experimental_P.pak/.utoc/.ucas` and restoring the user's chosen
reference mod. No original game files are edited.
