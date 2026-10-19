# Buzz V2: proportion and normal-texture revision

V1 is now a user-tested runtime baseline on Grounded 2 WinGDK0.316.9020.0: launch, Max replacement, textures/face/suit, walking, running, jumping, crouching, punching and chair sitting all worked, with no observed crashes. [The runtime record](windows-buzz-v1-test-0.316.9020.0.json) preserves that scope. Its ZIP and trio are unchanged. V2 is a separate test, not yet tested in-game.

## Findings

The source-to-stage audit finds geometry distortion in the original anatomical fit, not the export or cooked writer. V1 authoring-to-export position error is below0.000014cm and native read-back positions exactly match the compiled arrays. V1 torso widths used scales as low as0.52; limb transverse scales were0.72-0.75. Aligning eyes to Max used head scales1.055/0.544/0.642, changing the supplied face's proportions. Mapping a source ankle center0.224m high to the reference foot bone0.109m high stretched the shin and squashed the boot. These were fitting choices and should not be mistaken for runtime retarget corruption.

There is also a confirmed normal-texture defect. V1's intended constant BC5 normal block decodes to alternating columns of RG128/128 and255/255. The ISPC BC5 call received the wrong interleaved channel layout for this use. The extreme alternating normal directions explain the regular stripes and must not be treated as a speculative tangent issue. V1's old tests checked encoded mip hashes and color decode but did not validate flat-normal pixel contents. V2 writes two explicit constant BC4 blocks for each BC5 block, and its final validator independently checks RG128 across every mip. A regression reproduced V1's bad block before checking the replacement. Direct engine-style signed-normal decoding of tangent-buffer data differs from the intended normals by less than0.012; the working tangent encoder was left unchanged.

## Incremental correction

V2's `--style buzz-v2` option retains V1's default fitter for reproduction. It uses uniform0.9 head scaling instead of Max eye matching, broader torso and limb shells, larger gloves and boots, and rigid spherical elbow/knee pieces instead of blending those rigid joint shells across two bones. The visual ankle is raised to retain the source boot's height and reduce calf stretching. Shoulder/elbow and lateral leg visual offsets are documented in the fit report; the 230 reference bone transforms themselves are unchanged. This is a visual mesh correction, not a new animation retarget system.

Examples in meters (bounding axes, not universal anatomical dimensions):

| Component | Source | V1 | V2 |
| --- | ---: | ---: | ---: |
| Connected torso/head shell width | .875 | .457 | .744 |
| Thigh width | .212 | .159 | .222 |
| Shin height | .486 | .647 | .488 |
| Main boot height | .223 | .108 | .201 |

Max's fixed animation joint spacing still constrains exact Toy Story proportions. The supplied source model also has its own stylization. V2 makes targeted corrections without claiming a perfect match or predicting every game pose. Facial expressions remain unimplemented. Actual seated contact, equipment alignment, feet and hands need the next Windows test.

## Verification and previews

The separate V2 Blender file is `/workspace/mod-work/rig-stage/skinned-stowed-v2-proportions/Buzz-Grounded2-skinned.blend`. It was independently reopened and passed the existing10 controlled-pose tests, independent NumPy LBS checks and rigid-distance checks. All230rest matrices, eight packed textures, both six-object wing archives and exact original source wing coordinates/transforms were checked. Original extended panels remain hidden, backpack visible. No source scene or working V1 file was overwritten.

[Front, side and synthetic sitting previews](Buzz-V2-front-side-sitting.png) were rendered and inspected before ZIP creation and shown in chat. The source comparison render uses unchanged source vertex coordinates with a facing rotation/translation and the approved wing visibility omission. These are neutral Blender views, not actual game animations, shaders or collision/contact tests.

New cooked meshes contain18,780 render vertices and20,124 triangles each. The same native LOD/Zen writer, material references and retoc packaging workflow were used. Final verification/readback covers14packages/19chunks, actual native positions/indices/UVs/weights/palettes/normals/colors/material slots, private MI texture parameter/hash links, original external game imports, all50mips and decoded constant normal pixels. Source-to-V2-export error remains below0.000014cm. The original source images produce the **exact same color atlas PNG** as V1.

Against V1, only four shared chunks change: body mesh, backpack mesh, normal export and normal bulk. Fourteen shared chunks—including material instance, color/RMA/SSS textures, physics and hair—are byte-identical. The new mod basename has a new container header identity. The [delta report](buzz-v2-baseline-delta.json), [audit](buzz-v2-proportion-audit.json) and [final validation](buzz-v2-validation.json) record these checks. Changes to geometry and normal texture are bundled into one incremental gameplay candidate; separate causes are established offline rather than guessing from screenshots.

## Windows test

The separately named `Buzz-Lightyear-V2-Proportions-Test.zip` includes the zBuzzAtlasV2_P trio, instructions, SHA-256 checksums, audit/validation and front/side/sitting/source previews. Its manifest is [here](buzz-v2-release-manifest.json). User authorization to publish test ZIPs carries forward; V1's public ZIP remains unchanged.

Close the game. Move the entire old V1 trio (`zBuzzAtlasTest_P`) and any other Max skin overrides outside the **entire** `Augusta/Content/Paks` tree, retaining backups. Copy only zBuzzAtlasV2_P.pak/.utoc/.ucas directly into Paks. Do not touch originals or global containers. To roll back, close the game, remove the V2 trio and restore V1. Test under similar lighting, especially standing front/side, seated, crouching and punching. V2 runtime compatibility and visual improvement remain unconfirmed until the user reports results.

## Reproduce

Use new output paths; existing artifacts are immutable. Core commands from the existing source/rig stage:

```sh
python pipeline/fit_buzz_rig.py /workspace/mod-work/rig-stage/landmarks NEW_FIT --style buzz-v2
python pipeline/prepare_stowed_wings.py NEW_FIT NEW_STOWED
blender -b /workspace/mod-work/buzz-stage/final-inspection/Buzz-source-and-reference-skeleton.blend \
 --python-exit-code 1 --python pipeline/build_buzz_rig_blender.py -- NEW_STOWED NEW_SKINNED
```

Fresh-reopen validation and rendering follow the existing rig workflow. Validation expects the preserved `landmarks` folder adjacent to the skinned/fit directories, and a fit directory matching the skinned directory name with `skinned` replaced by `fit`.

```sh
blender -b NEW_SKINNED/Buzz-Grounded2-skinned.blend --python-exit-code 1 \
 --python pipeline/validate_buzz_rig.py -- NEW_SKINNED NEW_VALIDATION --no-render
blender -b -t 4 NEW_SKINNED/Buzz-Grounded2-skinned.blend --python-exit-code 1 \
 --python pipeline/render_buzz_shape_review.py -- NEW_SKINNED NEW_PREVIEWS
```

Export, repeat-aware atlas, native buffers, full LOD writer, corrected texture writer, direct Zen private-material isolation and packing reuse the documented V1 steps. `pipeline/readback_buzz_package.py NEW_STAGE PACKAGE_WORK` now automates the metadata/skeleton extraction, two independent native LOD reads, legacy conversion context and four texture mip-chain reads. `validate_buzz_atlas_final.py` checks final streams; put a `source-geometry.npz` link in NEW_STAGE to its source render export for independent affine UV reconstruction. V2's complete retained stage is `/workspace/mod-work/buzz-v2-stage`; no new original game extraction or mapping generation is needed.
