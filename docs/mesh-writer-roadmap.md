# Grounded 2 Buzz replacement: current state

The user-tested Commander101 `zMeshTest_P` launch/render/animation result is
recorded in [the Windows test report](windows-test-0.316.9020.0.json).
The delivered Max test ZIP remains unchanged. Its helmet-bump A/B comparison is
still inconclusive; the successful fixed-size test does not prove Buzz compatibility.

## Completed beyond that test

- Fitted the supplied real Buzz OBJ to the original 230-bone rest pose, including
  anatomical landmarks, hands/fingers, eye alignment and correction to Blender -Y.
- Transferred real Commander weights with anatomical restrictions and rigid armor
  overrides. Reopened and numerically validated the saved Blender file, textures,
  skeleton, weights, rigid attachments and ten controlled poses. Reviewed all
  front/back and pose renders. [Rigging details](buzz-rigging.md),
  [numerical results](buzz-rig-validation.json), [visual review](buzz-visual-review.json).
- Implemented the user's approved initial wing state: visible backpack, omitted
  extended panels. Six original source panels retain exact coordinates/transforms
  and six fitted extended panels retain chest-only weights in hidden collections.
  Candidate deployment points/hierarchy are documented; deployment is not implemented.
- Encoded new topology, normals/tangents, UVs, colors, indices and weights; serialized
  both complete resized inline LODs and their section/bone metadata. Relocated Zen
  skeletal-export sizes and the affected zero-size bulk-data-map offsets; updated
  bounds while preserving native skeleton/material/physics references and empty tails.
- Independently read both complete assets through CUE4Parse after IoStore repacking,
  compared decoded data against expected buffers, verified retoc Zen header readback,
  round-tripped all 26 chunks, and converted all 17 packages with zero failures.
  [Full-package results](resized-package-validation.json) and
  [reproduction commands](resized-package-pipeline.md).

The source rig has 12,957 vertices, 20,124 triangles, eight material slots and eight
packed textures. The encoded mesh has 19,609 render vertices, seven used sections,
230 required and 63 active bones. Original input was 13,450 vertices/20,482 triangles;
only a tiny marker, two degenerate triangles and the approved 328 wing-panel faces
are omitted from the visible mesh. Wings remain preserved separately.

This establishes a working **offline** resized mesh/Zen/IoStore pipeline for the
two measured Commander101 layouts. It does not establish arbitrary UE5.6 project
cooking, populated cloth/morph/Nanite resources, or runtime Buzz compatibility.
The old standalone-buffer reports describe their creation-time limited scope;
current full-package results supersede their "not implemented" integration status.

## Remaining work

1. **Compatible cooked materials/textures.** Blender's packed images are not cooked
   Unreal materials. The experimental package still has original Commander/Max
   material references; source Buzz material IDs do not select the right textures.
   Inspect original game material parents/parameters, or test a baked atlas with
   an existing proven parent plus a native texture-mip writer. Known texture formats
   are DXT5 base color, BC5 normals, DXT1 RMA/SSS. The original game material-instance
   packages are external to the uploaded mods; exact paths and the retained targeted
   local extraction helper are documented in `resized-package-pipeline.md`.
2. **Windows in-game validation.** Test new topology/skin deformation, actual
   animations, equipment, hands, seating, render bounds and clipping in build
   0.316.9020.0. Current sitting/crouching/running/climbing poses are approximations.
   Game movement, collision, inputs and gliding assets were not changed.
3. Refine any observed rig/material problems, then deliver the finished textured
   Buzz trio and installation/removal instructions. Facial-expression animation is
   not implemented. Wing controls/glider deployment and the other three characters
   remain deferred.

The source archive's conflicting license notices are recorded in
[buzz-intake.json](buzz-intake.json). Source model, texture, Blender and generated
Buzz mod payloads remain local; they have not been uploaded to this public repository.

**No finished textured or in-game-tested Buzz mod is claimed.** The local
`zBuzzGeometry_Experimental_P` trio is a geometry/package test with original material
references, despite its successful independent offline validation.
