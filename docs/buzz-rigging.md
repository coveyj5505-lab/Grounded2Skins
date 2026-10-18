# Buzz rig and initial wing state

The initial playable design uses a visible backpack with the six extended wing
panels excluded from the render mesh. The user approved this reversible approach.
No controls, gliding, movement, collision, new bones, or deployment animations are
implemented. This is a static visibility variant, not a physically folded mechanism.

## Preserved authoring geometry

The saved Blender project contains:

- `Buzz_Skinned`: visible, anatomically fitted, weighted mesh, 12,957 vertices,
  20,124 triangles, eight material slots and eight packed source textures.
- `Grounded2_Armature_230`: the original 230 bones and original rest matrices.
- `Wings_Original_Source_UNTOUCHED`: six original panels, 430 vertices and 328
  triangles. Exact source coordinates, UVs, materials and original object matrices;
  no fitting or new weights. Hidden from viewport/render, not deleted.
- `Wings_Extended_PRESERVED_NOT_EXPORTED`: six fitted extended panels, independently
  attached rigidly to `chest_JNT` (208). Hidden and excluded from the initial mesh.

To inspect either wing collection, enable its viewport visibility and unhide its
objects. Export scripts select `Buzz_Skinned` explicitly; they do not silently
include hidden authoring panels. Original supplied archives and the unmodified
inspection Blender file remain separate and untouched.

A deterministic search tested 1,001 orientations for each representative large
panel against the convex backpack envelope. It did not establish clean packing of
all panels. The test is a finite search, not proof that physical folding is
impossible. The approved visibility variant avoids protrusion or hidden
interpenetrating stacks without shrinking/deleting the original panels.

## Future deployment candidates, not an implemented mechanism

`wing-deployment-candidates.json` records source and fitted positions and matrices
for every panel. Candidate pivots are the average of vertices within 3 mm of its
inboard edge (minimum absolute source X). Likely authoring hierarchy:

| Panel component | Role | Candidate parent |
|---|---|---|
| 12 | Inner/root panel | Backpack/chest |
| 0 | Outer panel | 12 |
| 1 | Tip/detail | 0 |
| 51 | Inner/root panel | Backpack/chest |
| 62 | Outer panel | 51 |
| 72 | Tip/detail | 62 |

These are geometric hints. No verified hinge axis, telescoping path, internal
mechanism, simultaneous clearances, runtime skeleton extension, or animation
binding exists. Tip/detail parts probably need rigid parenting rather than their
own hinges. Future deployment must preserve the game's animation contract and
will require separate animation/runtime work; none is part of this initial mod.

## Fitting and skinning

Native reference nose/toes face Blender **-Y**. The earlier +Y inspection scene was
only an intake preview. The fit corrects facing, aligns joint/eye/digit landmarks,
and adapts Buzz's T-pose to the existing human rest pose. Source proportions are
adapted; this is not an unchanged movie-proportioned Buzz model.

Original Commander101 weights are sampled with region-restricted nearest-neighbor
transfer. Armor components, palms, boots and backpack receive explicit rigid
attachments; elbows/knees/ankles and digits receive constrained blends. A supplied
face material separates the head from its connected rigid collar. Neck material
seams are intentionally soft. No arbitrary root-only weighting is substituted.
The visible rig uses at most five nonzero influences per vertex; the native codec
supports eight. Face/eyes follow the head; facial expressions are not implemented.

The scripts preserve all 230 original rest matrices. Hash:
`9f5fdc5fe294ebc2b7277536292437fb01346700f3dcbe54a5b9f8b3759450ac`.
Native skeleton signature:
`204fba7a92cf816c84af30417b78b6e6f6d11716c3071611fffedb8b30a7a46a`.

## Reproduce from retained workspace artifacts

External Python requires NumPy/SciPy; Blender 4.3.2 provides its own NumPy.
Every output directory must be new. Existing originals are never overwritten.
From the repository root, use an isolated new stage directory:

```bash
stage=/workspace/mod-work/rig-stage-NEW
mkdir "$stage"
blender -b /workspace/mod-work/buzz-stage/final-inspection/Buzz-source-and-reference-skeleton.blend --python-exit-code 1 --python pipeline/inspect_rig_landmarks.py -- "$stage/landmarks"
python pipeline/fit_buzz_rig.py "$stage/landmarks" "$stage/fit" --reference-buffers /workspace/mod-work/mesh-stage/body
python pipeline/prepare_stowed_wings.py "$stage/fit" "$stage/fit-stowed"
blender -b /workspace/mod-work/buzz-stage/final-inspection/Buzz-source-and-reference-skeleton.blend --python-exit-code 1 --python pipeline/build_buzz_rig_blender.py -- "$stage/fit-stowed" "$stage/skinned-stowed"
blender -b "$stage/skinned-stowed/Buzz-Grounded2-skinned.blend" --python-exit-code 1 --python pipeline/validate_buzz_rig.py -- "$stage/skinned-stowed" "$stage/validation"
blender -b "$stage/skinned-stowed/Buzz-Grounded2-skinned.blend" --python-exit-code 1 --python pipeline/export_buzz_geometry.py -- /workspace/mod-work/global-stage/reports/reference-skeletons.json "$stage/skinned-stowed/build-report.json" "$stage/export" --skinned
python pipeline/native_buffers.py "$stage/export/Buzz-geometry-SKINNED.npz" /workspace/mod-work/global-stage/reports/reference-skeletons.json "$stage/native-buffers"
```

The validator independently reopens the saved file, checks geometry/UVs/materials,
packed images, normalized weights, source wing preservation and the original rest
hash. Controlled poses test Blender deformation against an independent NumPy LBS
calculation, rigid-piece distances and backpack independence from arm movement.
Sitting/crouching/running/climbing are synthetic approximations, not actual game
animation or collision tests. Numerical checks alone do not prove visual quality;
inspect the generated front/back and pose renders.

The source archive's conflicting license notices remain recorded in
`buzz-intake.json`. Source model/texture/Blender payloads remain local and are not
published to the public source repository.
