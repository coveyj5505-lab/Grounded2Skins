# Jessie V2 — focused deformation correction

**Offline validated, not yet tested in Grounded 2.** Jessie still replaces Hoops on the same PC Game Pass / WinGDK build 0.316.9020.0. V1, Buzz and Bo Peep files are preserved unchanged.

## Install / revert

Close the game. Move all three old `zJessieTest_P` files outside `Augusta\Content\Paks`, keeping them as your fallback. Also move any other Hoops replacement, including SuperEvie's trio, outside Paks. Do not install V1 and V2 together.

Extract `Jessie-Hoops-V2-Test.zip`, then copy the three files from its `mod` folder directly into `Augusta\Content\Paks`:

- `zJessieV2_P.pak`
- `zJessieV2_P.utoc`
- `zJessieV2_P.ucas`

Keep your working Buzz and Bo Peep installed. Select Hoops. Test standing, walking, running, sitting, crouching, jumping, punching, equipment grips and backpack toggling. Please compare arm/cuff positions and chaps attachment against V1. To revert, close the game, remove only the V2 trio, and restore your saved V1 trio. No original game files need replacement.

## Diagnosis supported by the source and native read-back

The source FBX has a Biped rig whose upper-arm twist helpers are parented under the clavicle, and forearm twist helpers under the upper arm. V1's nearest-mapped-ancestor fallback therefore assigned upper-arm twist weights to the **shoulder** and forearm twist weights to the **upper arm**, rather than their anatomical segments. This affected sleeves, cuffs and wrist-adjacent surfaces. V1 then fitted vertices using a sum of source-group transforms; the differently stretched/rotated transforms distorted clothing seams and body proportions. Some clothing edges reached 3.44 times their source length; clavicle/upper-torso fit factors exceeded2.0.

The actual stock Hoops mesh-local skeleton remains189 bones, with its original hierarchy/rest transforms. Blender bone/group order was checked against that table. The original source body is in rest pose; only imported eye pose bones have nonidentity pose bases. Those eyes/head assets are preserved. V1's cooked positions match its encoded geometry, so transport/serialization did not introduce the fitting distortion. No evidence warrants changing the working native buffer format, shaders, animation assets or game physics.

## Focused changes

- Correct left/right upper-arm and forearm twist group mapping by anatomical role, rather than parent ancestry.
- Fit upper/lower arm surfaces through a common positional field with preserved transverse width, avoiding V1's incompatible per-group geometry transforms.
- Use one consistent leg field for pants and chaps, with same-side hip/knee/ankle weighting. Small decorative pieces use near-rigid weights only when their source dimensions are under9cm; long low-vertex denim-leg components remain smoothly weighted.
- Widen the torso with one coherent fit (horizontal1.35, vertical approximately1.544), retaining fixed game joint spacing. This reduces extreme local stretching; it is not an exact whole-body animation retarget or a promise of unchanged source proportions everywhere.
- Preserve2,139 accepted source head/face/hat/hair/eye vertices and their V1 weights exactly. That corresponds to3,337 render vertices in each cooked body mesh. All UVs and triangle source indices remain exact V1.
- Preserve the original source hand silhouette with predominantly rigid hand weighting. Individual finger articulation is simplified; small wrist/base blends remain. This favors stability over perfect weapon grips.

No head reshaping, texture replacement, material-reference change, animation/skeleton/physics override or gameplay change is introduced. All thirteen unrelated non-header chunks—private MI/textures/bulk and hair replacements—are byte-exact V1. Only body/backpack mesh chunks change; the new package also has its own container identity.

## Validation actually completed

Fresh Blender reopen verifies4,883 vertices /8,757 triangles, native bone/group order, normalized saved weights, exact preserved atlas UVs and four packed images. An explicit source-anatomy check finds zero leg-bone influence across861 arm/hand vertices. Independent NumPy linear skinning agrees with Blender on all checked poses within3.8e-7m. Exaggerated +/-75-degree digit curls move the mostly rigid hand surfaces by less than0.5mm from residual blends.

Identical world-space FK joint directions were applied to V1 and V2 for standing, sitting and running. Those V2 previews were visually inspected, along with rest front/side and seated side. They show corrected cuffs/arms and continuous leg/chaps surfaces in these synthetic poses. They are **not captured game animations**. A source-nearest-vertex attachment sample checks80 denim/chaps pairs: V2's maximum sampled separation stays about3.1cm through the tested poses, consistent with wider clothing. That metric does not prove every garment surface is collision-free or that separation is lower than V1 everywhere.

Compared with source edge lengths, the99th-percentile stretch drops from2.23 to1.55 on the main outfit and2.36 to1.60 on the skin mesh. Peak local stretch also drops but is not eliminated. Native joint spacing still limits exact source proportions.

The complete new11-package /16-chunk IoStore verifies and unpacks to staged hashes. CUE4Parse independently reads all24 LODs across the two body and four hair assets. Positions, indices, section palettes, weights, UVs, colors and stock bone tables match intended encoding. Independent cooked comparison proves the accepted head positions/weights, every triangle's source vertex IDs and every native UV remain exact V1. All50 texture mips and material bindings still read correctly. Tangent/normal errors remain below0.004 with exact handedness signs. Actual cooked decoded front/side previews are included.

Only the Windows test can establish whether the remaining real game animation states look acceptable. Possible remaining limits: simplified finger grips, collar/shoulder creases, cloth clipping in untested poses, original Hoops first-person/menu/voice assets and the existing simple shared lighting/eye material. No full facial animation or secondary clothing/braid physics is added.

## Preserved source and reproduction

Original Jessie FBX/PNGs, V1 scene and V1 ZIP remain untouched. Final private V2 scene: `/workspace/mod-work/jessie-v2-stage/fit-v4/Jessie-Hoops-V2.blend`. Earlier V2 fit/controlled stages1–3 are diagnostics and are not distributed.

1. `audit_jessie_v1.py` on the original `jessie-stage/rig-v6` exports source coordinates, skeleton/weights/components and measured fitting distortion.
2. `correct_jessie_v2.py NEW_FIT` on the original `jessie-stage/gameplay-v1/Jessie-Hoops-gameplay.blend` creates corrected geometry/weights and expected arrays without editing the original file.
3. `review_jessie_v2_poses.py NEW_POSES` separately on preserved V1 and corrected V2 makes matching world-space FK poses. `validate_saved_jessie_v2.py EXPECTED SKIN POSES NEW_REPORT` independently reopens and checks source/weights/LBS. `measure_jessie_v2.py V2_ROOT NEW_REPORT` records exact accepted-head/UV preservation and sampled clothing attachment behavior.
4. Reuse `export_jessie_geometry.py`, `native_buffers.py`, `write_hoops_lods.py`, `assemble_jessie_zen.py`, and `repackage_iostore.py --mod-name zJessieV2_P`. Use original stock Hoops profiles and the unchanged V1 private material templates. All outputs must be new directories.
5. `readback_jessie_package.py`, then `validate_jessie_final.py ... --source-geometry NEW_GEOMETRY_NPZ`; `validate_jessie_v2_package.py V2_ROOT NEW_REPORT` proves the V1 delta and unchanged other releases. Reuse the native frame probe and cooked preview renderer.

Final V2 stage names: `fit-v4`, `controlled-v4`, `geometry-v4`, `buffers-v4`, `cooked-v4`, `raw-v4`, `package-v4`, `final-check-v4`, `frames-v4`. Atlas/stock symlinks point read-only to V1 inputs. Source assets and Blender files remain private; reusable scripts, reports and test files are preserved in the repository. Woody source preparation is also retained while this correction takes priority.
