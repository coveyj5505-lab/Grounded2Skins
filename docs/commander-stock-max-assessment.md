# Commander101 provenance and stock-Max compatibility assessment

Commander101 is a **third-party custom skin replacing Max**, not original game
art. Earlier descriptions of an "original 230-bone Max skeleton" were too strong:
we recovered Commander101's embedded mesh reference skeleton, not a verified copy
of stock Max's reference pose. No stock-Max equality claim is currently justified.
The new atlas test ZIP is paused at the user's requested compatibility gate.

## What was actually checked

All 17 supplied Commander101 asset packages and their exported classes were
inventoried using the original-game global script-object metadata:

| Export class | Count |
|---|---:|
| SkeletalMesh | 5 (two body variants plus three hair meshes) |
| Texture2D | 8 |
| PhysicsAsset | 4 |
| SkeletalBodySetup | 18 |
| PhysicsConstraintTemplate | 17 |
| AnimCurveMetaData | 2 |

There are **no Skeleton, AnimSequence, AnimBlueprint,
AnimBlueprintGeneratedClass or AnimMontage exports**. AnimCurveMetaData is auxiliary
metadata, not replacement animation tracks or an animation blueprint.

The body variants replace these existing game package paths:

```
/Game/_Augusta/Art/Characters/Player_Male01/SK_Male_Teen_01
/Game/_Augusta/Art/Characters/Player_Male01/SK_Male_Teen_01_w_BackPack
```

Their Zen import tables resolve to original-game packages including:

```
/Game/_Augusta/Art/Characters/Player_Male01/SK_Male_Teen_01_Skeleton
/Game/_Augusta/Art/Animation/AnimationBlueprints/AB_Player_Deformer_PostProcess
```

Serialized object-reference candidates in their unversioned property prefixes
match those imports and the backpack physics asset. Property labels are not
fully UObject-mapped; the report distinguishes that limitation from verified
import-table resolution. No replacement skeleton or animation blueprint is
included to override those original-game dependencies.

The recovered body and backpack **230-bone names, order, parent hierarchy and
parent-local translation/quaternion/scale records are exactly equal**. Both
rewritten Buzz assets preserve that same native reference-skeleton byte range
and their unversioned property prefixes exactly. This directly verifies that
our writer has not altered the recovered skeleton/animation/physics settings.
Local scale deviations from unity are at most 4.77e-7, consistent with floating
precision; they are not evidence of a meaningful scale edit.

See [the machine-readable assessment](commander-compatibility-assessment.json).

## How this works with game animation

A skeletal mesh's embedded `FReferenceSkeleton` describes its bone names,
parents and bind/rest pose. Its section palettes map skin influences into that
mesh bone table. The referenced game `USkeleton`, animation blueprints and tracks
supply animation data; Unreal links mesh and skeleton bones by name/hierarchy.
The player/pawn blueprint and primary animation setup are not replaced by these
art packages. The imported post-process blueprint also remains game-provided.

A mod **can** refer to the original USkeleton while having a modified mesh-local
rest pose, different proportions, extra bones or different weights. Retargeting
settings and pose composition can accommodate some differences. Consequently,
"same external Skeleton path" and "animations play" do **not** prove exact stock
bone hierarchy/rest-pose identity or perfect deformation in every animation.

The user's Commander101 and `zMeshTest_P` launch/render/animation tests establish
useful observed compatibility for those tested mods. Buzz's own controlled poses
prove its skinning calculations and rigid attachments, not runtime compatibility
with all original game animations, equipment, first-person or post-process behavior.

## What is not yet known

The actual original-game Max mesh and USkeleton packages are absent from current
uploads. The supplied `global` container holds script-object metadata, not Max's
bone hierarchy/rest transforms. Therefore we cannot yet answer whether Commander
retained stock Max's local pose exactly, or modified it while retaining the game
USkeleton reference. No meaningful stock-vs-mod differences have been established
because the stock side of that comparison is missing.

Commander also includes a replacement backpack PhysicsAsset and three hair
PhysicsAssets. We preserved those Commander bytes; that is not proof of stock
skeletal-physics equality. The mod contains no player/pawn/capsule/movement assets.
Hair hiding and skeletal/ragdoll physics must not be confused with player capsule
collision or movement mechanics.

## Safest path; no unnecessary restart

1. Keep the present Buzz mesh, eight source textures, weights, preserved wings,
   source Blender file, variable-buffer encoder, complete LOD writer, Zen relocation
   and proven retoc packaging workflow. None needs discarding now.
2. Compare original Max's body/backpack mesh reference skeletons and USkeleton by
   bone name, index/order, parent and sign-invariant local rest transforms. Equal
   quaternions with opposite signs must not be flagged as different rotations.
   Separately inspect the stock physics asset and original material instance.
3. If the stock mesh pose matches, continue the existing rig/atlas pipeline.
   No skeleton rebuild is needed. Original Max's material setup is the authoritative
   source for verifying the atlas sampler and later isolating material instances.
4. If meaningful weighted-bone/parent/pose differences appear, report their exact
   locations/magnitudes before a major change. Reuse existing fitting/weight data
   with an explicit bone-name mapping or controlled rebind to the stock target,
   then rerun pose/native checks. Extra unweighted bones or order differences
   alone do not automatically require recreating the model.

The original Max mesh is a better **verification baseline**, not a reason to
replace a known-working cooked template with an unverified new UE project/cook.
Stock material/physics assets can resolve questions the third-party mod cannot.

## Small original-game extraction needed from Windows

[Stock-Max-Compatibility-Extractor.zip](../Stock-Max-Compatibility-Extractor.zip)
contains source scripts only. It selects five packages (plus only their own bulk
chunks) from the exact original `Augusta-WinGDK.utoc` and adjacent UCAS:

```
/Game/_Augusta/Art/Characters/Player_Male01/SK_Male_Teen_01
/Game/_Augusta/Art/Characters/Player_Male01/SK_Male_Teen_01_w_BackPack
/Game/_Augusta/Art/Characters/Player_Male01/SK_Male_Teen_01_Skeleton
/Game/_Augusta/Art/Characters/Player_Male01/SK_Male_Teen_01_w_BackPack_PhysicsAsset
/Game/_Augusta/Art/Characters/Player_Male01/Textures/MI_Character_Male01_Max_Apparel01
```

Unzip it, run `Start-Extraction.cmd`, choose Windows retoc0.1.5 and the original
UTOC. Python3.11+ is required. It creates a Desktop ZIP for sharing. It does not
edit game files or installed mods, and does not use Paks-folder override context,
so Commander101 cannot substitute for original Max during extraction. Details
and requirements are in its README. The Windows dialog wrapper itself cannot be
run in this Linux cloud environment.

The underlying extractor was exercised here against Commander101 as an explicit
negative control: exactly three available packages were selected; the absent
stock Skeleton/material were reported; the dataset was rejected as stock evidence.
The bone comparer also passed sign-equivalent quaternion, wrist-translation and
parent-change calibration checks. These controls are not original-game evidence.

After those actual original packages arrive:

```bash
python pipeline/compare_stock_max.py /path/to/extracted-original-assets \
 /workspace/mod-work/global-stage/reports/reference-skeletons.json \
 /workspace/mod-work/buzz-test-stage/NEW-stock-comparison
```

The script checks package provenance/hashes, structurally reads native reference
skeletons and produces per-bone comparison results. Unsupported layouts fail
explicitly rather than guessing. Material/physics headers are inventoried, not
misrepresented as fully deserialized shader/shape data.

## Preserved atlas progress

All eight source images remain unchanged. A repeat-aware atlas, remapped UVs,
new native buffers and four mod-contained texture mip chains have been staged.
An independent CUE4Parse texture reader successfully read the original 13-mip
base-color chain using actual serialized header/bulk metadata without UObject
property mappings. Final modified-texture/package validation, exact original
material sampler verification and the installable test ZIP remain pending.
No finalized Buzz gameplay test is claimed, and no movement/input/gliding or
wing-deployment feature has been implemented.
